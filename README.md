# escape-tab
An escape room in a browser tab. Solve 3 competition math problems in order to exit. 

## How It Works
Pulls AMC10,12, and AIME problems from a bank (scraped from AOPS' website) and then converts each problem to an html fragment using katex. 
Problems are selected at random, 3 at a time. 

Uses the PointerClick API to disable your operating system's native cursor. A "Problem Solved" count is incremented for each one of your successful solves. When you hit 3 solved problems, your cursor functionality is restored and you're free to leave. Or to play again :P
