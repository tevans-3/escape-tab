# escape-tab
An escape room in a browser tab. Solve 3 competition math problems in order to exit the tab.

## How It Works
Uses this person's [CITATION] web-scraping script to fetch every past American Mathematics Competition problem from the Art of Problem Solving's 
website, and then converts each problem to an html fragment using Latex.js. Problems are selected at random from the bank of html fragments. 

Uses the PointerClick API to disable your operating system's native cursor. A "Problem Solved" count is incremented for each one of your successful solves. 
When you hit 10 solved problems, your cursor functionality is restored and you're free to leave. Or to play again :P
