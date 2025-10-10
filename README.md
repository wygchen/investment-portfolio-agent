## Git commit procedure
Git and GitHub are two different things. You have to install Git first.

Use source control tab for easier management but the logic is same as using command line, self-learn how to use source control tab

Only commit working code and do not directly commit to main branch

Command line reference for each commit:
```Bash
git pull #always pull before commit
git status #check that you are on the correct branch
git checkout branch #to change branch
git status #double check the branch, super large files should not be committed, add the corresponding file type to .gitignore
git add . #add all remaining files to the commit
git status #always double check
git commit -m "message" # write meaningful commit message
git status #always double check
git push #this is the action to upload to the "drive"
```

Final reminder: GitHub can be disastrous. If any error occurs find github copilot, it is very good at command line actions. If github copilot want to perform dangerous actions such as revert commit, ask in group first we might face similar things before TT
