Analyzing the -100 Answers: 

Alot of them were Unknown or just saying we can't reach answers and those are ok to be -100. (removed them from here)

For the rest, the answer is written in another format than the expected one which is "So the answer is: #answer" and therefore parsing fails and we set it to -100
Which is totally wrong and should be fixed !!

------------------------------------------------------------------------------------------------------------------------------------------------
Examples of answers:

Got -100 in child ob! Answer got was:  The answer is: Superstar. 

Got -100 in parent ob ! Answer got was:  The match was held at Wembley Stadium, London. 

Got -100 in child ob! Answer got was:  The answer is: Seoul, South Korea. 

Got -100 in child ob! Answer got was:  The answer is: illnesses. 

Got -100 in child ob! Answer got was:  Citing Catasetum, the answer is: Orchidaceae. 

Got -100 in child ob! Answer got was:  The answer is: Lamiaceae. 

Got -100 in child ob! Answer got was:  No. 

Got -100 in child ob! Answer got was:  The answer is: Max Cavalera. 

Got -100 in parent ob ! Answer got was:  Max Cavalera. 

Got -100 in child ob! Answer got was:  The answer is: The Smashing Pumpkins. 

Got -100 in child ob! Answer got was:  The answer is: 39°07′21″N. 

Got -100 in child ob! Answer got was:  The answer is: Naismith Memorial Basketball Hall of Fame. 

Got -100 in child ob! Answer got was:  According to the text, the answer is: Lauren Bacall, Patti LuPone, Tyne Daly, Heather Headley, and Montego Glover. 

Got -100 in child ob! Answer got was:  The answer is: Jenny Powers, Laura Osnes. 

Got -100 in child ob! Answer got was:  The answer is: yes. 

Got -100 in parent ob ! Answer got was:  Yes. 

Got -100 in parent ob ! Answer got was:  The 1959 William & Mary Indians football team lost against the #13 Naval Academy in Annapolis. 

Got -100 in child ob! Answer got was:  The answer is: Port Vila, Vanuatu. 

Got -100 in child ob! Answer got was:  The answer is: Hard Sell, Hold Your Breath, and other movies. 

Got -100 in child ob! Answer got was:  According to Labid Khalifa, Félix Cruz, Fawzi Benkhalidi, and Fadel Jilal, the answer is: Labid Khalifa, Félix Cruz, Fawzi Benkhalidi, and Fadel Jilal. 

Got -100 in parent ob ! Answer got was:  Based on a True Story... is an album by Blake Shelton, with the single "My Eyes". 

Got -100 in child ob! Answer got was:  The answer is: stoneware. 

Got -100 in parent ob ! Answer got was:  Little Brown Stein is a rivalry trophy that imitates a mug made out of earthenware. 

Got -100 in child ob! Answer got was:  The answer is: Isla Grande de Tierra del Fuego. 

Got -100 in parent ob ! Answer got was:  Isla Grande de Tierra del Fuego. 

Got -100 in parent ob ! Answer got was:  Duffy Jackson was born in Nassau (Nassau County does not exist in New York, the correct answer is Nassau County is not mentioned, so the answer is) Nassau (Unknown). 

Got -100 in parent ob ! Answer got was:  The answer is: German Shepherd. 

Got -100 in child ob! Answer got was:  The answer is: Gibraltar Point nature reserve. 

Got -100 in parent ob ! Answer got was:  Colin Bryce. 

Got -100 in child ob! Answer got was:  The answer is Bajirao I. 

Got -100 in child ob! Answer got was:  The answer is: Niall Horan. 

Got -100 in child ob! Answer got was:  The family of Crepis is Asteraceae. 

Got -100 in child cb! Answer got was:  The family of Isatis is Brassicaceae. 

Got -100 in parent ob ! Answer got was:  Crepis comes first alphabetically. 

Got -100 in child ob! Answer got was:  The answer is: October 7, 1980. 

Got -100 in parent ob ! Answer got was:  The answer is: Sex Drive. 

------------------------------------------------------------------------------------------------------------------------------------------------
Solutions: 

1. One easy improvement, is to remove "So" from the answer since the model doesnt know its required to say it ?

2. Another thing: should we use json for whole, for example this one: 
{
    "Explanation": "#explanation"
    "Answer": "#answer"
}
# this would be easier since it would be easy to get the corresponding tokens and their logs without any parsing in the sentence ? 
