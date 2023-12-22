from bardapi import Bard

bard = Bard(token="egihLdsiDZ84lZ7vLBBZKNpkNoiMeW7olDmd2PR26qVgYP8uMkcox94CascfZuyDv5N94w.")
res = bard.get_answer("Do you like cookies?")
print(res['content'])