document.addEventListener('DOMContentLoaded', function() {
    const verbosityDescriptions = {
        classDoc: [
            "No docstrings for classes.",
            "Very brief, one-line comments for major classes only.",
            "Concise but informative docstrings for classes, covering basic purposes and functionality.",
            "Detailed docstrings including parameters, return types, and a description of the class behavior.",
            "Very detailed explanations, including usage examples in the docstrings.",
            "Extremely detailed docstrings, providing in-depth explanations, usage examples, and covering edge cases."
        ],
        functionDoc: [
        "No docstrings for classes.",
        "Very brief, one-line comments for major classes only.",
        "Concise but informative docstrings for classes, covering basic purposes and functionality.",
        "Detailed docstrings including parameters, return types, and a description of the class behavior.",
        "Very detailed explanations, including usage examples in the docstrings.",
        "Extremely detailed docstrings, providing in-depth explanations, usage examples, and covering edge cases."
        ],
        example: [
            "No examples.",
            "Simple examples demonstrating basic usage.",
            "More comprehensive examples covering various use cases.",
            "Detailed examples with step-by-step explanations.",
            "Extensive examples including edge cases and error handling.",
            "Interactive examples or code playgrounds for experimentation."
        ]
    };

    function mapHtmlNameToVerbosityKey(htmlName) {
        const mapping = {
            'class-doc': 'classDoc',
            'function-doc': 'functionDoc',
            'example': 'example'
        };
        return mapping[htmlName];
    }
    
    function updateVerbosityDescription(verbosityHtmlName, value) {
        const verbosityType = mapHtmlNameToVerbosityKey(verbosityHtmlName);
        let desc = verbosityDescriptions[verbosityType][value];
        document.getElementById(`${verbosityHtmlName}-verbosity-desc`).textContent = desc;
    }
    
    // Event listeners for sliders
    document.getElementById('class-doc-verbosity').addEventListener('input', function() {
        document.getElementById('class-doc-verbosity-value').textContent = this.value;
        updateVerbosityDescription('class-doc', this.value);
    });

    document.getElementById('function-doc-verbosity').addEventListener('input', function() {
        document.getElementById('function-doc-verbosity-value').textContent = this.value;
        updateVerbosityDescription('function-doc', this.value);
    });
    
    document.getElementById('example-verbosity').addEventListener('input', function() {
        document.getElementById('example-verbosity-value').textContent = this.value;
        updateVerbosityDescription('example', this.value);
    });    

    updateVerbosityDescription('class-doc', document.getElementById('class-doc-verbosity-value').textContent);
    updateVerbosityDescription('function-doc', document.getElementById('function-doc-verbosity-value').textContent);
    updateVerbosityDescription('example', document.getElementById('example-verbosity-value').textContent);

    var editor = ace.edit("editor");

    // Set theme to Monokai (you can choose other themes)
    editor.setTheme("ace/theme/monokai");

    // Set mode to Python for Python syntax highlighting
    editor.session.setMode("ace/mode/python");

    // Python-specific configurations
    editor.setOptions({
        // Enable basic autocompletion and snippets
        enableBasicAutocompletion: true,
        enableSnippets: true,
        // Use soft tabs with a tab size of 4, as per PEP8 guidelines
        useSoftTabs: true,
        tabSize: 4,
        // Show line numbers and enable code folding
        showLineNumbers: true,
        enableLiveAutocompletion: true, // Requires additional extension
        foldStyle: 'markbegin' // Code folding
    });

    // Optional: Adjust editor height based on content
    // editor.setOption("maxLines", 100);
    editor.setOption("minLines", 10);

    // Optional: Disable print margin
    editor.setShowPrintMargin(false);

    // Optional: Highlight active line
    editor.setHighlightActiveLine(true);

    editor.setOption("fontSize", "16px"); 

    // Initialize Highlight.js for static code blocks
    hljs.highlightAll();

    document.getElementById('botSelectionForm').addEventListener('submit', function(event) {
        event.preventDefault();  // Prevent the default form submission


        var code = getCodeFromEditor();
        var selectedBots = Array.from(document.querySelectorAll('input[name="chatbot"]:checked')).map(input => input.value);
        var userCode = code

        // Send data to process_code endpoint
        sendCodeToServer(userCode, selectedBots);

        // Initialize streams for selected bots
        selectedBots.forEach(botName => {
            initializeBotStream(botName);
        });
    });
});

function sendCodeToServer(code, chatbots) {
    fetch('/process_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ code: code, chatbots: chatbots })
    })
    .then(response => {
        if (!response.ok) {
            // Response is not OK, attempt to parse the JSON body for the error message
            return response.json().then(err => {
                showError(err.error_message || `Server responded with a status: ${response.status}`);
            });
        }
        return response.json(); // If response is OK, parse it as JSON
    })
    .then(data => {
        if (data.is_valid) {
            // Display the processed code in a Python code control
            displayProcessedCode(code);
        } else {
            // Handle API-provided error
            showError(data.error_message);
        }
    })
    .catch(error => showError(error.message)); // Display the error message
}


// Function to display an error message
function showError(errorMessage) {
    var errorDiv = document.getElementById('error_messages');
    errorDiv.textContent = errorMessage; // Set the text content of the div to the error message
    errorDiv.style.display = 'block';    // Change display from 'none' to 'block' to show the div
}


function showError(errorMessage) {
    var errorDiv = document.getElementById('error_messages');
    errorDiv.textContent = errorMessage; // Set the text content of the div to the error message
    errorDiv.style.display = 'block';    // Change display from 'none' to 'block' to show the div
}

function initializeBotStream(botName) {
    var eventSource = new EventSource('/stream/' + botName);
    eventSource.onmessage = function(event) {
        // Check if the message is an APIResponse indicating an error
        try {
            var data = JSON.parse(event.data);
            if (data && !data.is_valid) {
                showError(data.error);
                eventSource.close();  // Close the stream if there is an error
                updateUIForError(botName, data.error); // Update UI to show the error
            } else {
                // Handle regular data
                var botDiv = document.getElementById('chatbot_' + botName + '_messages');
                botDiv.innerHTML += data.message + '<br>';  // Assuming the regular message is in data.message
            }
        } catch (e) {
            // If parsing fails, it's regular data, not a JSON error message
            var botDiv = document.getElementById('chatbot_' + botName + '_messages');
            botDiv.innerHTML += event.data + '<br>';
        }
    };
}

function updateUIForError(botName, errorMessage) {
    // Implement how you want to show the error in the UI
    var errorDiv = document.getElementById('error_message');
    errorDiv.innerHTML = `Error in ${botName}: ${errorMessage}`;
    errorDiv.style.display = 'block';
}


function displayProcessedCode(code) {
    var codeDiv = document.getElementById('processed_code');  // Assuming you have a div with ID 'processed_code'
    codeDiv.innerHTML = '<pre><code class="python">' + code + '</code></pre>';
    // Apply syntax highlighting if using a library like highlight.js
}

var editor = ace.edit("editor");
editor.setTheme("ace/theme/monokai");  // Set theme
editor.session.setMode("ace/mode/python");  // Set language mode (Python in this case)

// Function to retrieve the code from the editor
function getCodeFromEditor() {
    return editor.getValue();
}

function toggleChatbotSection(botName) {
    var checkbox = document.getElementById('chatbot_' + botName);
    var container = document.getElementById('chatbot_' + botName + '_container');

    if (checkbox.checked) {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

