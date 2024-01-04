from clang.cindex import CursorKind
from clang.cindex import Index, TranslationUnit
from clang.cindex import Cursor

# Example usage
CursorKind(8)


class CppCodeProcessor:
    def __init__(self):
        self.index = Index.create()

    def parse_cpp_code(self, code: str):
        # Create an unsaved file with the source code
        unsaved_files = [('temp.cpp', code)]
        # Parse the source code to create a translation unit
        tu = self.index.parse('temp.cpp', unsaved_files=unsaved_files,
                              options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
        # Return the root cursor of the AST
        return tu.cursor
        
    def _prepare_insertions(self, tree, content_lines, docstrings):
        pass
        # insertions = {}
        # for node in tree.get_children():
        #     if node.kind in [CursorKind.FUNCTION_DECL, CursorKind.CXX_METHOD, CursorKind.CLASS_DECL]:
        #         start_line = node.extent.start.line - 1
        #         indent_level = 4 + self._get_indent(content_lines[start_line])
        #         class_or_func_name = node.spelling

        #         if node.kind == CursorKind.CLASS_DECL and class_or_func_name in docstrings:
        #             class_doc = docstrings[class_or_func_name]
        #             if "docstring" in class_doc:
        #                 insertions[start_line] = self._format_docstring(class_doc["docstring"], indent_level)

        #             if "methods" in class_doc:
        #                 for method_node in node.get_children():
        #                     if method_node.kind == CursorKind.CXX_METHOD and method_node.spelling in class_doc["methods"]:
        #                         method_start_line = method_node.extent.start.line - 1
        #                         method_indent_level = 4 + self._get_indent(content_lines[method_start_line])
        #                         method_doc = class_doc["methods"][method_node.spelling]
        #                         insertions[method_start_line] = self._format_docstring(method_doc, method_indent_level)

        #         elif node.kind == CursorKind.FUNCTION_DECL and 'global_functions' in docstrings:
        #             if class_or_func_name in docstrings['global_functions']:
        #                 func_doc = docstrings['global_functions'][class_or_func_name]
        #                 insertions[start_line] = self._format_docstring(func_doc, indent_level)

        # return insertions

    def format_docstring(self, docstring: str, indent_level: int) -> str:
        # Format the docstring with the appropriate indentation
        indent = ' ' * indent_level
        formatted_docstring = '\n'.join([indent + line for line in docstring.split('\n')])
        return f"/*\n{formatted_docstring}\n{indent}*/"

    def get_indent_level(self, node):
        """
        Get the indentation level of the given node.
        """
        # Assuming you have a way to get the full source code line where the node starts
        source_code = self.get_source_code()  # Implement this method to return the full source code as a list of lines
        start_line_number = node.extent.start.line - 1  # Convert to zero-based index
        line = ''
        if source_code:
            line = source_code[start_line_number]
        return self._get_indent(line)

    def _get_indent(self, line):
        """
        Get the number of leading whitespace characters in the line.
        """
        return len(line) - len(line.lstrip())

    def insert_docstrings(self, content, docstrings):
        pass
        # content_lines = content.split('\n')
        # tree = self.parse_cpp_code(content)  # Parse the C++ code

        # insertions = self._prepare_insertions(tree, content_lines, docstrings)

        # new_content = []
        # for i, line in enumerate(content_lines):
        #     new_content.append(line)
        #     if i in insertions:
        #         # Properly extend the list with the docstring lines
        #         new_content.extend(insertions[i].split('\n'))

        # return '\n'.join(new_content)

    # Example method to get full source code (to be implemented as needed)
    def get_source_code(self):
        # Return the full source code as a list of lines
        pass
