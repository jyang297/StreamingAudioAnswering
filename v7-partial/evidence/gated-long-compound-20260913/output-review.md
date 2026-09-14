# Builder output review



AI-authored diagnostic export; semantic judgments require reading each row.



## long:california_schools:87 / snapshot 0

Input: What

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:california_schools:87 / snapshot 1

Input: What are the valid e-mail addresses of the administrator of the school located in

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "87", "question": "What are the valid e-mail addresses of the administrator of the school located in the San Bernardino county, San Bernardino city that opened between 1/1/2009 to 12/31/2010 which is also both an Intermediate/Middle School and Unified School? List the valid emails in two columns.", "cosine": 0.8004763277273731}

Normalized top candidate: null



## long:california_schools:87 / snapshot 2

Input: What are the valid e-mail addresses of the administrator of the school located in the San Bernardino county, San Bernardino city that opened between 1/1/2009 to 12/31/2010 which is

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "87", "question": "What are the valid e-mail addresses of the administrator of the school located in the San Bernardino county, San Bernardino city that opened between 1/1/2009 to 12/31/2010 which is also both an Intermediate/Middle School and Unified School? List the valid emails in two columns.", "cosine": 0.9673708222648838}

Normalized top candidate: null



## long:california_schools:87 / snapshot 3

Input: What are the valid e-mail addresses of the administrator of the school located in the San Bernardino county, San Bernardino city that opened between 1/1/2009 to 12/31/2010 which is also both an Intermediate/Middle School and Unified School? List the valid emails in two columns.

Context: []

Builder: {"action": "search", "question": "What are the valid e-mail addresses of the administrator of the school located in San Bernardino county, San Bernardino city that opened between 1/1/2009 to 12/31/2010 which is also both an Intermediate/Middle School and Unified School? List the valid emails in two columns."}

Raw top candidate: {"id": "87", "question": "What are the valid e-mail addresses of the administrator of the school located in the San Bernardino county, San Bernardino city that opened between 1/1/2009 to 12/31/2010 which is also both an Intermediate/Middle School and Unified School? List the valid emails in two columns.", "cosine": 1.0}

Normalized top candidate: {"id": "87", "question": "What are the valid e-mail addresses of the administrator of the school located in the San Bernardino county, San Bernardino city that opened between 1/1/2009 to 12/31/2010 which is also both an Intermediate/Middle School and Unified School? List the valid emails in two columns.", "cosine": 0.99941987676882}



## long:california_schools:32 / snapshot 0

Input: What

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:california_schools:32 / snapshot 1

Input: What is the eligible free or reduced price meal rate for

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "32", "question": "What is the eligible free or reduced price meal rate for the top 5 schools in K-12 with the highest free or reduced price meal count of the schools with the ownership code 66?", "cosine": 0.740476700004424}

Normalized top candidate: null



## long:california_schools:32 / snapshot 2

Input: What is the eligible free or reduced price meal rate for the top 5 schools in K-12 with the highest free or

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "32", "question": "What is the eligible free or reduced price meal rate for the top 5 schools in K-12 with the highest free or reduced price meal count of the schools with the ownership code 66?", "cosine": 0.9522423821379746}

Normalized top candidate: null



## long:california_schools:32 / snapshot 3

Input: What is the eligible free or reduced price meal rate for the top 5 schools in K-12 with the highest free or reduced price meal count of the schools with the ownership code 66?

Context: []

Builder: {"action": "search", "question": "What is the eligible free or reduced price meal rate for the top 5 K-12 schools with the highest free or reduced price meal count among schools with ownership code 66?"}

Raw top candidate: {"id": "32", "question": "What is the eligible free or reduced price meal rate for the top 5 schools in K-12 with the highest free or reduced price meal count of the schools with the ownership code 66?", "cosine": 0.9999999549577159}

Normalized top candidate: {"id": "32", "question": "What is the eligible free or reduced price meal rate for the top 5 schools in K-12 with the highest free or reduced price meal count of the schools with the ownership code 66?", "cosine": 0.9954602720041135}



## compound:california_schools / snapshot 0

Input: Which

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## compound:california_schools / snapshot 1

Input: Which state special schools have the highest number of enrollees from K-12?

Context: []

Builder: {"action": "search", "question": "Which state special schools have the highest number of K-12 enrollees?"}

Raw top candidate: {"id": "72", "question": "How many students from the ages of 5 to 17 are enrolled at State Special School schools in Fremont for the 2014-2015 academic year?", "cosine": 0.7375204878842916}

Normalized top candidate: {"id": "72", "question": "How many students from the ages of 5 to 17 are enrolled at State Special School schools in Fremont for the 2014-2015 academic year?", "cosine": 0.7292772746958418}



## compound:california_schools / snapshot 2

Input: Which state special schools have the highest number of enrollees from K-12? Also, What is the grade span offered

Context: []

Builder: {"action": "search", "question": "Which state special schools have the highest number of K-12 enrollees, and what grade span do they offer?"}

Raw top candidate: {"id": "72", "question": "How many students from the ages of 5 to 17 are enrolled at State Special School schools in Fremont for the 2014-2015 academic year?", "cosine": 0.7436012475015753}

Normalized top candidate: {"id": "72", "question": "How many students from the ages of 5 to 17 are enrolled at State Special School schools in Fremont for the 2014-2015 academic year?", "cosine": 0.7533796479019045}



## compound:california_schools / snapshot 3

Input: Which state special schools have the highest number of enrollees from K-12? Also, What is the grade span offered in the school with the highest longitude?

Context: []

Builder: {"action": "search", "question": "Which state special schools have the highest number of K-12 enrollees, and what is the grade span offered in the school with the highest longitude?"}

Raw top candidate: {"id": "82", "question": "What is the grade span offered in the school with the highest longitude?", "cosine": 0.7487675083456832}

Normalized top candidate: {"id": "82", "question": "What is the grade span offered in the school with the highest longitude?", "cosine": 0.7909765684573207}



## long:debit_card_specializing:1481 / snapshot 0

Input: What

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:debit_card_specializing:1481 / snapshot 1

Input: What is the difference in the annual average consumption of the

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1498", "question": "What is the highest monthly consumption in the year 2012?", "cosine": 0.7249920037329887}

Normalized top candidate: null



## long:debit_card_specializing:1481 / snapshot 2

Input: What is the difference in the annual average consumption of the customers with the least amount of consumption paid in CZK for

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1471", "question": "What is the ratio of customers who pay in EUR against customers who pay in CZK?", "cosine": 0.688683246938558}

Normalized top candidate: null



## long:debit_card_specializing:1481 / snapshot 3

Input: What is the difference in the annual average consumption of the customers with the least amount of consumption paid in CZK for 2013 between SME and LAM, LAM and KAM, and KAM and SME?

Context: []

Builder: {"action": "search", "question": "What is the difference in the annual average consumption of the customers with the least amount of consumption paid in CZK for 2013 between SME and LAM, LAM and KAM, and KAM and SME?"}

Raw top candidate: {"id": "1482", "question": "Provide the percentage increase in consumption paid in EUR between 2012 and 2013 for SME, LAM, and KAM respectively.", "cosine": 0.7765991923548036}

Normalized top candidate: {"id": "1482", "question": "Provide the percentage increase in consumption paid in EUR between 2012 and 2013 for SME, LAM, and KAM respectively.", "cosine": 0.7765991923548036}



## long:debit_card_specializing:1531 / snapshot 0

Input: Who

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:debit_card_specializing:1531 / snapshot 1

Input: Who is the top spending customer and how

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1531", "question": "Who is the top spending customer and how much is the average price per single item purchased by this customer? What currency was being used?", "cosine": 0.8032453471463563}

Normalized top candidate: null



## long:debit_card_specializing:1531 / snapshot 2

Input: Who is the top spending customer and how much is the average price per single item

Context: []

Builder: {"action": "search", "question": "Who is the top spending customer and how much is the average price per single item?"}

Raw top candidate: {"id": "1531", "question": "Who is the top spending customer and how much is the average price per single item purchased by this customer? What currency was being used?", "cosine": 0.8700034459798459}

Normalized top candidate: {"id": "1531", "question": "Who is the top spending customer and how much is the average price per single item purchased by this customer? What currency was being used?", "cosine": 0.8781964832562303}



## long:debit_card_specializing:1531 / snapshot 3

Input: Who is the top spending customer and how much is the average price per single item purchased by this customer? What currency was being used?

Context: []

Builder: {"action": "search", "question": "Who is the top spending customer, how much is the average price per single item purchased by this customer, and what currency was being used?"}

Raw top candidate: {"id": "1531", "question": "Who is the top spending customer and how much is the average price per single item purchased by this customer? What currency was being used?", "cosine": 0.9999999620656824}

Normalized top candidate: {"id": "1531", "question": "Who is the top spending customer and how much is the average price per single item purchased by this customer? What currency was being used?", "cosine": 0.9961808536744838}



## compound:debit_card_specializing / snapshot 0

Input: In

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## compound:debit_card_specializing / snapshot 1

Input: In 2012, who had the least consumption in LAM?

Context: []

Builder: {"action": "search", "question": "In 2012, who had the least consumption in LAM?"}

Raw top candidate: {"id": "1472", "question": "In 2012, who had the least consumption in LAM?", "cosine": 0.999999923732297}

Normalized top candidate: {"id": "1472", "question": "In 2012, who had the least consumption in LAM?", "cosine": 0.999999923732297}



## compound:debit_card_specializing / snapshot 2

Input: In 2012, who had the least consumption in LAM? Also, What segment did the

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1472", "question": "In 2012, who had the least consumption in LAM?", "cosine": 0.9644020894651105}

Normalized top candidate: null



## compound:debit_card_specializing / snapshot 3

Input: In 2012, who had the least consumption in LAM? Also, What segment did the customer have at 2012/8/23 21:20:00?

Context: []

Builder: {"action": "search", "question": "In 2012, who had the least consumption in LAM? Also, what segment did the customer have at 2012/8/23 21:20:00?"}

Raw top candidate: {"id": "1472", "question": "In 2012, who had the least consumption in LAM?", "cosine": 0.9160375563424037}

Normalized top candidate: {"id": "1472", "question": "In 2012, who had the least consumption in LAM?", "cosine": 0.9169409304197249}



## long:financial:149 / snapshot 0

Input: Please

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:financial:149 / snapshot 1

Input: Please list the account types that are not eligible for loans,

Context: []

Builder: {"action": "search", "question": "Which account types are not eligible for loans?"}

Raw top candidate: {"id": "149", "question": "Please list the account types that are not eligible for loans, and the average income of residents in the district where the account is located exceeds $8000 but is no more than $9000.", "cosine": 0.7703701221164183}

Normalized top candidate: {"id": "149", "question": "Please list the account types that are not eligible for loans, and the average income of residents in the district where the account is located exceeds $8000 but is no more than $9000.", "cosine": 0.7228431515307346}



## long:financial:149 / snapshot 2

Input: Please list the account types that are not eligible for loans, and the average income of residents in the district where the

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "149", "question": "Please list the account types that are not eligible for loans, and the average income of residents in the district where the account is located exceeds $8000 but is no more than $9000.", "cosine": 0.9182394991331175}

Normalized top candidate: null



## long:financial:149 / snapshot 3

Input: Please list the account types that are not eligible for loans, and the average income of residents in the district where the account is located exceeds $8000 but is no more than $9000.

Context: []

Builder: {"action": "search", "question": "Which account types are not eligible for loans, where the average income of residents in the district where the account is located exceeds $8000 but is no more than $9000?"}

Raw top candidate: {"id": "149", "question": "Please list the account types that are not eligible for loans, and the average income of residents in the district where the account is located exceeds $8000 but is no more than $9000.", "cosine": 0.9999999494084133}

Normalized top candidate: {"id": "149", "question": "Please list the account types that are not eligible for loans, and the average income of residents in the district where the account is located exceeds $8000 but is no more than $9000.", "cosine": 0.9503744030217439}



## long:financial:152 / snapshot 0

Input: What

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:financial:152 / snapshot 1

Input: What is the average number of crimes committed in 1995

Context: []

Builder: {"action": "search", "question": "What is the average number of crimes committed in 1995?"}

Raw top candidate: {"id": "152", "question": "What is the average number of crimes committed in 1995 in districts where the number exceeds 4000 and the district has accounts that are opened starting from the year 1997?", "cosine": 0.835669561375507}

Normalized top candidate: {"id": "152", "question": "What is the average number of crimes committed in 1995 in districts where the number exceeds 4000 and the district has accounts that are opened starting from the year 1997?", "cosine": 0.8435330342130622}



## long:financial:152 / snapshot 2

Input: What is the average number of crimes committed in 1995 in districts where the number exceeds 4000 and the district

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "152", "question": "What is the average number of crimes committed in 1995 in districts where the number exceeds 4000 and the district has accounts that are opened starting from the year 1997?", "cosine": 0.9454346649496812}

Normalized top candidate: null



## long:financial:152 / snapshot 3

Input: What is the average number of crimes committed in 1995 in districts where the number exceeds 4000 and the district has accounts that are opened starting from the year 1997?

Context: []

Builder: {"action": "search", "question": "What is the average number of crimes committed in 1995 in districts where the number of crimes exceeds 4000 and the district has accounts that are opened starting from the year 1997?"}

Raw top candidate: {"id": "152", "question": "What is the average number of crimes committed in 1995 in districts where the number exceeds 4000 and the district has accounts that are opened starting from the year 1997?", "cosine": 1.0}

Normalized top candidate: {"id": "152", "question": "What is the average number of crimes committed in 1995 in districts where the number exceeds 4000 and the district has accounts that are opened starting from the year 1997?", "cosine": 0.9873447695537368}



## compound:financial / snapshot 0

Input: How

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## compound:financial / snapshot 1

Input: How many accounts have running contracts in Branch location 1?

Context: []

Builder: {"action": "search", "question": "How many accounts have running contracts in Branch location 1?"}

Raw top candidate: {"id": "173", "question": "How often does account number 3 request an account statement to be released? What was the aim of debiting 3539 in total?", "cosine": 0.5860078617670139}

Normalized top candidate: {"id": "173", "question": "How often does account number 3 request an account statement to be released? What was the aim of debiting 3539 in total?", "cosine": 0.5860078617670139}



## compound:financial / snapshot 2

Input: How many accounts have running contracts in Branch location 1? Also, What percentage of clients who request

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "173", "question": "How often does account number 3 request an account statement to be released? What was the aim of debiting 3539 in total?", "cosine": 0.5970687259860117}

Normalized top candidate: null



## compound:financial / snapshot 3

Input: How many accounts have running contracts in Branch location 1? Also, What percentage of clients who request weekly statements to be issued are male?

Context: []

Builder: {"action": "search", "question": "How many accounts have running contracts in Branch location 1, and what percentage of clients who request weekly statements to be issued are male?"}

Raw top candidate: {"id": "186", "question": "What percentage of clients who request weekly statements to be issued are male?", "cosine": 0.7499153518693491}

Normalized top candidate: {"id": "186", "question": "What percentage of clients who request weekly statements to be issued are male?", "cosine": 0.789485771684522}



## long:formula_1:880 / snapshot 0

Input: Paul

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:formula_1:880 / snapshot 1

Input: Paul di Resta was in the No. 853 race,

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "880", "question": "Paul di Resta was in the No. 853 race, what percent faster did he finish in the 853rd race than the next race for the fastest lap speed?", "cosine": 0.7463660120072682}

Normalized top candidate: null



## long:formula_1:880 / snapshot 2

Input: Paul di Resta was in the No. 853 race, what percent faster did he finish in the 853rd

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "880", "question": "Paul di Resta was in the No. 853 race, what percent faster did he finish in the 853rd race than the next race for the fastest lap speed?", "cosine": 0.9387479931641372}

Normalized top candidate: null



## long:formula_1:880 / snapshot 3

Input: Paul di Resta was in the No. 853 race, what percent faster did he finish in the 853rd race than the next race for the fastest lap speed?

Context: []

Builder: {"action": "search", "question": "In the No. 853 race, what percent faster was Paul di Resta's fastest lap speed than his fastest lap speed in the next race?"}

Raw top candidate: {"id": "880", "question": "Paul di Resta was in the No. 853 race, what percent faster did he finish in the 853rd race than the next race for the fastest lap speed?", "cosine": 0.9999999541276378}

Normalized top candidate: {"id": "880", "question": "Paul di Resta was in the No. 853 race, what percent faster did he finish in the 853rd race than the next race for the fastest lap speed?", "cosine": 0.9590117731732871}



## long:formula_1:1002 / snapshot 0

Input: As

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:formula_1:1002 / snapshot 1

Input: As of the present, what is the full name

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1001", "question": "What is full name of the racer who ranked 1st in the 3rd qualifying race held in the Marina Bay Street Circuit in 2008?", "cosine": 0.3586621762736269}

Normalized top candidate: null



## long:formula_1:1002 / snapshot 2

Input: As of the present, what is the full name of the youngest racer? Indicate her nationality and the

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "877", "question": "For all the drivers who finished all laps of the game in race No. 872, who is the youngest?", "cosine": 0.7593109002768064}

Normalized top candidate: null



## long:formula_1:1002 / snapshot 3

Input: As of the present, what is the full name of the youngest racer? Indicate her nationality and the name of the race to which he/she first joined.

Context: []

Builder: {"action": "search", "question": "As of the present, what is the full name of the youngest racer, her nationality, and the name of the race to which she first joined?"}

Raw top candidate: {"id": "877", "question": "For all the drivers who finished all laps of the game in race No. 872, who is the youngest?", "cosine": 0.7196047284155274}

Normalized top candidate: {"id": "877", "question": "For all the drivers who finished all laps of the game in race No. 872, who is the youngest?", "cosine": 0.6837497008845791}



## compound:formula_1 / snapshot 0

Input: What's

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## compound:formula_1 / snapshot 1

Input: What's the location coordinates of Silverstone Circuit?

Context: []

Builder: {"action": "search", "question": "What are the location coordinates of Silverstone Circuit?"}

Raw top candidate: {"id": "910", "question": "What's the location coordinates of Silverstone Circuit?", "cosine": 0.9999999106829685}

Normalized top candidate: {"id": "910", "question": "What's the location coordinates of Silverstone Circuit?", "cosine": 0.9959501549504434}



## compound:formula_1 / snapshot 2

Input: What's the location coordinates of Silverstone Circuit? Also, Which country is

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "910", "question": "What's the location coordinates of Silverstone Circuit?", "cosine": 0.970458436090045}

Normalized top candidate: null



## compound:formula_1 / snapshot 3

Input: What's the location coordinates of Silverstone Circuit? Also, Which country is the oldest driver from?

Context: []

Builder: {"action": "search", "question": "What are the location coordinates of Silverstone Circuit, and which country is the oldest driver from?"}

Raw top candidate: {"id": "910", "question": "What's the location coordinates of Silverstone Circuit?", "cosine": 0.8468796920560445}

Normalized top candidate: {"id": "910", "question": "What's the location coordinates of Silverstone Circuit?", "cosine": 0.8480307360967239}



## long:student_club:1405 / snapshot 0

Input: List

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:student_club:1405 / snapshot 1

Input: List all the budgeted categories for the 'April

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1405", "question": "List all the budgeted categories for the 'April Speaker' event, along with their amount budgeted. Return the results in an ascending order of their amount budgeted.", "cosine": 0.7605172997173306}

Normalized top candidate: null



## long:student_club:1405 / snapshot 2

Input: List all the budgeted categories for the 'April Speaker' event, along with their amount budgeted. Return the

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1405", "question": "List all the budgeted categories for the 'April Speaker' event, along with their amount budgeted. Return the results in an ascending order of their amount budgeted.", "cosine": 0.9584447892788719}

Normalized top candidate: null



## long:student_club:1405 / snapshot 3

Input: List all the budgeted categories for the 'April Speaker' event, along with their amount budgeted. Return the results in an ascending order of their amount budgeted.

Context: []

Builder: {"action": "search", "question": "List all the budgeted categories for the 'April Speaker' event, along with their amount budgeted, in ascending order of their amount budgeted."}

Raw top candidate: {"id": "1405", "question": "List all the budgeted categories for the 'April Speaker' event, along with their amount budgeted. Return the results in an ascending order of their amount budgeted.", "cosine": 0.9999999503344568}

Normalized top candidate: {"id": "1405", "question": "List all the budgeted categories for the 'April Speaker' event, along with their amount budgeted. Return the results in an ascending order of their amount budgeted.", "cosine": 0.9665717048501166}



## long:student_club:1317 / snapshot 0

Input: Among

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:student_club:1317 / snapshot 1

Input: Among the students from the Student_Club who

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1322", "question": "Among the events attended by more than 10 members of the Student_Club, how many of them are meetings?", "cosine": 0.656701169374377}

Normalized top candidate: null



## long:student_club:1317 / snapshot 2

Input: Among the students from the Student_Club who attended the event "Women's Soccer", how many of

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1399", "question": "Did Maya Mclean attend the 'Women's Soccer' event? YES or NO.", "cosine": 0.6651869405045159}

Normalized top candidate: null



## long:student_club:1317 / snapshot 3

Input: Among the students from the Student_Club who attended the event "Women's Soccer", how many of them want a T-shirt that's in medium size?

Context: []

Builder: {"action": "search", "question": "Among the students from the Student_Club who attended the event \"Women's Soccer\", how many of them want a T-shirt that's in medium size?"}

Raw top candidate: {"id": "1432", "question": "Among the members with t-shirt size of medium, what is the percentage of the amount 50 received by the Student_Club?", "cosine": 0.6986620456873553}

Normalized top candidate: {"id": "1432", "question": "Among the members with t-shirt size of medium, what is the percentage of the amount 50 received by the Student_Club?", "cosine": 0.6986620456873553}



## compound:student_club / snapshot 0

Input: What's

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## compound:student_club / snapshot 1

Input: What's Angela Sanders's major?

Context: []

Builder: {"action": "search", "question": "What is Angela Sanders's major?"}

Raw top candidate: {"id": "1312", "question": "What's Angela Sanders's major?", "cosine": 0.9999999369801311}

Normalized top candidate: {"id": "1312", "question": "What's Angela Sanders's major?", "cosine": 0.9893864292324486}



## compound:student_club / snapshot 2

Input: What's Angela Sanders's major? Also, What was

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1312", "question": "What's Angela Sanders's major?", "cosine": 0.9619162536059547}

Normalized top candidate: null



## compound:student_club / snapshot 3

Input: What's Angela Sanders's major? Also, What was Brent Thomason's major?

Context: []

Builder: {"action": "search", "question": "What is Angela Sanders's major and what was Brent Thomason's major?"}

Raw top candidate: {"id": "1312", "question": "What's Angela Sanders's major?", "cosine": 0.9063357017167701}

Normalized top candidate: {"id": "1312", "question": "What's Angela Sanders's major?", "cosine": 0.8719811616646295}



## long:superhero:743 / snapshot 0

Input: What

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:superhero:743 / snapshot 1

Input: What is the percentage of superheroes who act in their own

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "760", "question": "In superheroes with height between 150 to 180, what is the percentage of heroes published by Marvel Comics?", "cosine": 0.8054230730595975}

Normalized top candidate: null



## long:superhero:743 / snapshot 2

Input: What is the percentage of superheroes who act in their own self-interest or make decisions based on their own moral code? Indicate

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "801", "question": "Find the ratio between male superheroes and female superheroes.", "cosine": 0.6998159464056508}

Normalized top candidate: null



## long:superhero:743 / snapshot 3

Input: What is the percentage of superheroes who act in their own self-interest or make decisions based on their own moral code? Indicate how many of the said superheroes were published by Marvel Comics.

Context: []

Builder: {"action": "search", "question": "What is the percentage of superheroes who act in their own self-interest or make decisions based on their own moral code, and how many of those superheroes were published by Marvel Comics?"}

Raw top candidate: {"id": "760", "question": "In superheroes with height between 150 to 180, what is the percentage of heroes published by Marvel Comics?", "cosine": 0.7076991700296478}

Normalized top candidate: {"id": "760", "question": "In superheroes with height between 150 to 180, what is the percentage of heroes published by Marvel Comics?", "cosine": 0.7845255397278146}



## long:superhero:744 / snapshot 0

Input: Between

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:superhero:744 / snapshot 1

Input: Between DC and Marvel Comics, which publisher

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "733", "question": "How many gold-eyed superheroes did Marvel Comics publish?", "cosine": 0.7594232664755185}

Normalized top candidate: null



## long:superhero:744 / snapshot 2

Input: Between DC and Marvel Comics, which publisher has published more superheroes? Find the difference

Context: []

Builder: {"action": "search", "question": "Between DC and Marvel Comics, which publisher has published more superheroes, and what is the difference in the number of superheroes published?"}

Raw top candidate: {"id": "733", "question": "How many gold-eyed superheroes did Marvel Comics publish?", "cosine": 0.8237516294521166}

Normalized top candidate: {"id": "733", "question": "How many gold-eyed superheroes did Marvel Comics publish?", "cosine": 0.8264047040618301}



## long:superhero:744 / snapshot 3

Input: Between DC and Marvel Comics, which publisher has published more superheroes? Find the difference in the number of superheroes they have published.

Context: []

Builder: {"action": "search", "question": "Between DC and Marvel Comics, which publisher has published more superheroes, and what is the difference in the number of superheroes they have published?"}

Raw top candidate: {"id": "733", "question": "How many gold-eyed superheroes did Marvel Comics publish?", "cosine": 0.768455089217291}

Normalized top candidate: {"id": "733", "question": "How many gold-eyed superheroes did Marvel Comics publish?", "cosine": 0.8201919879062294}



## compound:superhero / snapshot 0

Input: What

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## compound:superhero / snapshot 1

Input: What is Copycat's race?

Context: []

Builder: {"action": "search", "question": "What is Copycat's race?"}

Raw top candidate: {"id": "737", "question": "What is Copycat's race?", "cosine": 0.9999998977503671}

Normalized top candidate: {"id": "737", "question": "What is Copycat's race?", "cosine": 0.9999998977503671}



## compound:superhero / snapshot 2

Input: What is Copycat's race? Also, What is

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "737", "question": "What is Copycat's race?", "cosine": 0.9841061424607964}

Normalized top candidate: null



## compound:superhero / snapshot 3

Input: What is Copycat's race? Also, What is Abomination's superpower?

Context: []

Builder: {"action": "search", "question": "What is Copycat's race and what is Abomination's superpower?"}

Raw top candidate: {"id": "737", "question": "What is Copycat's race?", "cosine": 0.8457706881466446}

Normalized top candidate: {"id": "737", "question": "What is Copycat's race?", "cosine": 0.838112106418839}



## long:thrombosis_prediction:1189 / snapshot 0

Input: What

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:thrombosis_prediction:1189 / snapshot 1

Input: What number of patients with a degree of thrombosis level 2

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1157", "question": "For patients with severe degree of thrombosis, list their ID, sex and disease the patient is diagnosed with.", "cosine": 0.703333493826579}

Normalized top candidate: null



## long:thrombosis_prediction:1189 / snapshot 2

Input: What number of patients with a degree of thrombosis level 2 and ANA pattern of only S, have a level of anti-Cardiolip

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1267", "question": "Among the patients with normal anti-SM, how many of them does not have thrombosis?", "cosine": 0.6536062851262159}

Normalized top candidate: null



## long:thrombosis_prediction:1189 / snapshot 3

Input: What number of patients with a degree of thrombosis level 2 and ANA pattern of only S, have a level of anti-Cardiolip in antibody (IgM) 20% higher than average value of that same subgroup?

Context: []

Builder: {"action": "search", "question": "How many patients with thrombosis level 2 and ANA pattern of only S have an anti-Cardiolipin antibody (IgM) level 20% higher than the average anti-Cardiolipin antibody (IgM) value of that same subgroup?"}

Raw top candidate: {"id": "1251", "question": "How many patients with an Ig G higher than normal?", "cosine": 0.685315344058159}

Normalized top candidate: {"id": "1251", "question": "How many patients with an Ig G higher than normal?", "cosine": 0.6581468728241744}



## long:thrombosis_prediction:1192 / snapshot 0

Input: List

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:thrombosis_prediction:1192 / snapshot 1

Input: List all patients who were followed up at the outpatient

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1162", "question": "How many female patients who came at the hospital in 1997 was immediately followed at the outpatient clinic?", "cosine": 0.7126627072456987}

Normalized top candidate: null



## long:thrombosis_prediction:1192 / snapshot 2

Input: List all patients who were followed up at the outpatient clinic who underwent a laboratory test in October 1991 and

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1162", "question": "How many female patients who came at the hospital in 1997 was immediately followed at the outpatient clinic?", "cosine": 0.6645821958210808}

Normalized top candidate: null



## long:thrombosis_prediction:1192 / snapshot 3

Input: List all patients who were followed up at the outpatient clinic who underwent a laboratory test in October 1991 and had a total blood bilirubin level within the normal range.

Context: []

Builder: {"action": "search", "question": "List all patients who were followed up at the outpatient clinic who underwent a laboratory test in October 1991 and had a total blood bilirubin level within the normal range."}

Raw top candidate: {"id": "1225", "question": "List and group all patients by sex for total bilirubin (T-BIL) level not within the normal range. Return the sex and the corresponding group.", "cosine": 0.672182389133201}

Normalized top candidate: {"id": "1225", "question": "List and group all patients by sex for total bilirubin (T-BIL) level not within the normal range. Return the sex and the corresponding group.", "cosine": 0.672182389133201}



## compound:thrombosis_prediction / snapshot 0

Input: How

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## compound:thrombosis_prediction / snapshot 1

Input: How many female patients were given an APS diagnosis?

Context: []

Builder: {"action": "search", "question": "How many female patients were given an APS diagnosis?"}

Raw top candidate: {"id": "1162", "question": "How many female patients who came at the hospital in 1997 was immediately followed at the outpatient clinic?", "cosine": 0.6923347287300652}

Normalized top candidate: {"id": "1162", "question": "How many female patients who came at the hospital in 1997 was immediately followed at the outpatient clinic?", "cosine": 0.6923347287300652}



## compound:thrombosis_prediction / snapshot 2

Input: How many female patients were given an APS diagnosis? Also, How many patients with an

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "1162", "question": "How many female patients who came at the hospital in 1997 was immediately followed at the outpatient clinic?", "cosine": 0.6683276319818026}

Normalized top candidate: null



## compound:thrombosis_prediction / snapshot 3

Input: How many female patients were given an APS diagnosis? Also, How many patients with an Ig G higher than normal?

Context: []

Builder: {"action": "search", "question": "How many female patients were given an APS diagnosis, and how many patients had an IgG higher than normal?"}

Raw top candidate: {"id": "1251", "question": "How many patients with an Ig G higher than normal?", "cosine": 0.7525903611385265}

Normalized top candidate: {"id": "1251", "question": "How many patients with an Ig G higher than normal?", "cosine": 0.7463146403960144}



## long:toxicology:215 / snapshot 0

Input: How

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:toxicology:215 / snapshot 1

Input: How many atoms with iodine and with

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "215", "question": "How many atoms with iodine and with sulfur type elements, respectively, are there in molecules that contain at least one single bond?", "cosine": 0.837905373159148}

Normalized top candidate: null



## long:toxicology:215 / snapshot 2

Input: How many atoms with iodine and with sulfur type elements, respectively, are there in

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "215", "question": "How many atoms with iodine and with sulfur type elements, respectively, are there in molecules that contain at least one single bond?", "cosine": 0.9103394326454421}

Normalized top candidate: null



## long:toxicology:215 / snapshot 3

Input: How many atoms with iodine and with sulfur type elements, respectively, are there in molecules that contain at least one single bond?

Context: []

Builder: {"action": "search", "question": "How many atoms with iodine and with sulfur type elements, respectively, are there in molecules that contain at least one single bond?"}

Raw top candidate: {"id": "215", "question": "How many atoms with iodine and with sulfur type elements, respectively, are there in molecules that contain at least one single bond?", "cosine": 0.9999999999999999}

Normalized top candidate: {"id": "215", "question": "How many atoms with iodine and with sulfur type elements, respectively, are there in molecules that contain at least one single bond?", "cosine": 0.9999999999999999}



## long:toxicology:226 / snapshot 0

Input: What

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## long:toxicology:226 / snapshot 1

Input: What is the percentage of double bonds

Context: []

Builder: {"action": "search", "question": "What is the percentage of double bonds?"}

Raw top candidate: {"id": "226", "question": "What is the percentage of double bonds in the molecule TR008? Please provide your answer as a percentage with five decimal places.", "cosine": 0.620264877909664}

Normalized top candidate: {"id": "226", "question": "What is the percentage of double bonds in the molecule TR008? Please provide your answer as a percentage with five decimal places.", "cosine": 0.6435221528259281}



## long:toxicology:226 / snapshot 2

Input: What is the percentage of double bonds in the molecule TR008? Please provide your

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "226", "question": "What is the percentage of double bonds in the molecule TR008? Please provide your answer as a percentage with five decimal places.", "cosine": 0.9435758028570939}

Normalized top candidate: null



## long:toxicology:226 / snapshot 3

Input: What is the percentage of double bonds in the molecule TR008? Please provide your answer as a percentage with five decimal places.

Context: []

Builder: {"action": "search", "question": "What is the percentage of double bonds in the molecule TR008, expressed as a percentage with five decimal places?"}

Raw top candidate: {"id": "226", "question": "What is the percentage of double bonds in the molecule TR008? Please provide your answer as a percentage with five decimal places.", "cosine": 0.9999999386908784}

Normalized top candidate: {"id": "226", "question": "What is the percentage of double bonds in the molecule TR008? Please provide your answer as a percentage with five decimal places.", "cosine": 0.9545806220017258}



## compound:toxicology / snapshot 0

Input: What

Context: []

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## compound:toxicology / snapshot 1

Input: What is the most common bond type?

Context: []

Builder: {"action": "search", "question": "What is the most common bond type?"}

Raw top candidate: {"id": "195", "question": "What is the most common bond type?", "cosine": 0.9999999327710913}

Normalized top candidate: {"id": "195", "question": "What is the most common bond type?", "cosine": 0.9999999327710913}



## compound:toxicology / snapshot 2

Input: What is the most common bond type? Also, What elements are in

Context: []

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "195", "question": "What is the most common bond type?", "cosine": 0.9549099043108911}

Normalized top candidate: null



## compound:toxicology / snapshot 3

Input: What is the most common bond type? Also, What elements are in the TR004_8_9 bond atoms?

Context: []

Builder: {"action": "search", "question": "What is the most common bond type, and what elements are in the TR004_8_9 bond atoms?"}

Raw top candidate: {"id": "236", "question": "What are the bond type and the atoms of the bond ID of TR001_6_9?", "cosine": 0.8924514964882138}

Normalized top candidate: {"id": "236", "question": "What are the bond type and the atoms of the bond ID of TR001_6_9?", "cosine": 0.9075457035683373}



## synthetic:0 / snapshot 0

Input: And

Context: [{"role": "user", "content": "What is Abomination's superpower?"}]

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:0 / snapshot 1

Input: And Batman

Context: [{"role": "user", "content": "What is Abomination's superpower?"}]

Builder: {"gate": {"allow": false, "words": 2, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:0 / snapshot 2

Input: And Batman?

Context: [{"role": "user", "content": "What is Abomination's superpower?"}]

Builder: {"gate": {"allow": false, "words": 2, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:0 / snapshot 3

Input: And Batman?

Context: [{"role": "user", "content": "What is Abomination's superpower?"}]

Builder: {"action": "search", "question": "What is Batman's superpower?"}

Raw top candidate: {"id": "736", "question": "Who is the dumbest superhero?", "cosine": 0.6676052210326908}

Normalized top candidate: {"id": "764", "question": "What are the superpowers of heroes with ID 1?", "cosine": 0.625488619970034}



## synthetic:1 / snapshot 0

Input: And

Context: [{"role": "user", "content": "What was the average monthly consumption of customers in SME for the year 2013?"}]

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:1 / snapshot 1

Input: And 2012

Context: [{"role": "user", "content": "What was the average monthly consumption of customers in SME for the year 2013?"}]

Builder: {"gate": {"allow": false, "words": 2, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:1 / snapshot 2

Input: And 2012?

Context: [{"role": "user", "content": "What was the average monthly consumption of customers in SME for the year 2013?"}]

Builder: {"gate": {"allow": false, "words": 2, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:1 / snapshot 3

Input: And 2012?

Context: [{"role": "user", "content": "What was the average monthly consumption of customers in SME for the year 2013?"}]

Builder: {"action": "search", "question": "What was the average monthly consumption of customers in SME for the year 2012?"}

Raw top candidate: {"id": "1498", "question": "What is the highest monthly consumption in the year 2012?", "cosine": 0.5232000712866277}

Normalized top candidate: {"id": "1482", "question": "Provide the percentage increase in consumption paid in EUR between 2012 and 2013 for SME, LAM, and KAM respectively.", "cosine": 0.7213166777805476}



## synthetic:2 / snapshot 0

Input: What

Context: [{"role": "user", "content": "How many accounts opened in 1995?"}]

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:2 / snapshot 1

Input: What about 1996

Context: [{"role": "user", "content": "How many accounts opened in 1995?"}]

Builder: {"action": "search", "question": "How many accounts were opened in 1996?"}

Raw top candidate: {"id": "136", "question": "Between 1/1/1995 and 12/31/1997, how many loans in the amount of at least 250,000 per account that chose monthly statement issuance were approved?", "cosine": 0.4909899435538555}

Normalized top candidate: {"id": "136", "question": "Between 1/1/1995 and 12/31/1997, how many loans in the amount of at least 250,000 per account that chose monthly statement issuance were approved?", "cosine": 0.7214098883738711}



## synthetic:2 / snapshot 2

Input: What about 1996?

Context: [{"role": "user", "content": "How many accounts opened in 1995?"}]

Builder: {"action": "search", "question": "How many accounts opened in 1996?"}

Raw top candidate: {"id": "136", "question": "Between 1/1/1995 and 12/31/1997, how many loans in the amount of at least 250,000 per account that chose monthly statement issuance were approved?", "cosine": 0.4768427172016669}

Normalized top candidate: {"id": "136", "question": "Between 1/1/1995 and 12/31/1997, how many loans in the amount of at least 250,000 per account that chose monthly statement issuance were approved?", "cosine": 0.6998113229153773}



## synthetic:2 / snapshot 3

Input: What about 1996?

Context: [{"role": "user", "content": "How many accounts opened in 1995?"}]

Builder: {"action": "search", "question": "How many accounts were opened in 1996?"}

Raw top candidate: {"id": "136", "question": "Between 1/1/1995 and 12/31/1997, how many loans in the amount of at least 250,000 per account that chose monthly statement issuance were approved?", "cosine": 0.4768427172016669}

Normalized top candidate: {"id": "136", "question": "Between 1/1/1995 and 12/31/1997, how many loans in the amount of at least 250,000 per account that chose monthly statement issuance were approved?", "cosine": 0.7214098883738711}



## synthetic:3 / snapshot 0

Input: Who

Context: [{"role": "user", "content": "Who won the race in 2012?"}]

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:3 / snapshot 1

Input: Who won in 2013

Context: [{"role": "user", "content": "Who won the race in 2012?"}]

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "989", "question": "What was the finish time of the champion of the Canadian Grand Prix in 2008?", "cosine": 0.3918115270492773}

Normalized top candidate: null



## synthetic:3 / snapshot 2

Input: Who won in 2013, in Monaco?

Context: [{"role": "user", "content": "Who won the race in 2012?"}]

Builder: {"action": "search", "question": "Who won the race in Monaco in 2013?"}

Raw top candidate: {"id": "862", "question": "For the Bahrain Grand Prix in 2007, how many drivers not finished all laps of the game?", "cosine": 0.5143849599511153}

Normalized top candidate: {"id": "862", "question": "For the Bahrain Grand Prix in 2007, how many drivers not finished all laps of the game?", "cosine": 0.5714885444041882}



## synthetic:3 / snapshot 3

Input: Who won in 2013, in Monaco?

Context: [{"role": "user", "content": "Who won the race in 2012?"}]

Builder: {"action": "search", "question": "Who won in Monaco in 2013?"}

Raw top candidate: {"id": "862", "question": "For the Bahrain Grand Prix in 2007, how many drivers not finished all laps of the game?", "cosine": 0.5143849599511153}

Normalized top candidate: {"id": "862", "question": "For the Bahrain Grand Prix in 2007, how many drivers not finished all laps of the game?", "cosine": 0.5142126841678516}



## synthetic:4 / snapshot 0

Input: List

Context: [{"role": "user", "content": "List the events held in 2020."}]

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:4 / snapshot 1

Input: List the events in 2021

Context: [{"role": "user", "content": "List the events held in 2020."}]

Builder: {"action": "search", "question": "List the events in 2021"}

Raw top candidate: {"id": "1350", "question": "What is the status of the event which bought \"Post Cards, Posters\" on 2019/8/20?", "cosine": 0.5596080534379435}

Normalized top candidate: {"id": "1350", "question": "What is the status of the event which bought \"Post Cards, Posters\" on 2019/8/20?", "cosine": 0.5596080534379435}



## synthetic:4 / snapshot 2

Input: List the events in 2021, excluding fundraisers.

Context: [{"role": "user", "content": "List the events held in 2020."}]

Builder: {"action": "search", "question": "List the events in 2021, excluding fundraisers."}

Raw top candidate: {"id": "1323", "question": "List all the names of events that had an attendance of over 20 students but were not fundraisers.", "cosine": 0.5583694981589677}

Normalized top candidate: {"id": "1323", "question": "List all the names of events that had an attendance of over 20 students but were not fundraisers.", "cosine": 0.5583694981589677}



## synthetic:4 / snapshot 3

Input: List the events in 2021, excluding fundraisers.

Context: [{"role": "user", "content": "List the events held in 2020."}]

Builder: {"action": "search", "question": "List the events in 2021, excluding fundraisers."}

Raw top candidate: {"id": "1323", "question": "List all the names of events that had an attendance of over 20 students but were not fundraisers.", "cosine": 0.5583694981589677}

Normalized top candidate: {"id": "1323", "question": "List all the names of events that had an attendance of over 20 students but were not fundraisers.", "cosine": 0.5583694981589677}



## synthetic:5 / snapshot 0

Input: And

Context: [{"role": "user", "content": "How many schools are in Alameda?"}]

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:5 / snapshot 1

Input: And Los Angeles

Context: [{"role": "user", "content": "How many schools are in Alameda?"}]

Builder: {"action": "wait", "question": null}

Raw top candidate: {"id": "77", "question": "Which schools served a grade span of Kindergarten to 9th grade in the county of Los Angeles and what is its Percent (%) Eligible FRPM (Ages 5-17)?", "cosine": 0.3953859485577053}

Normalized top candidate: null



## synthetic:5 / snapshot 2

Input: And Los Angeles, only public schools?

Context: [{"role": "user", "content": "How many schools are in Alameda?"}]

Builder: {"action": "search", "question": "How many public schools are in Los Angeles?"}

Raw top candidate: {"id": "62", "question": "What is the total number of non-chartered schools in the county of Los Angeles with a percent (%) of eligible free meals for K-12 that is less than 0.18%?", "cosine": 0.6823609509787004}

Normalized top candidate: {"id": "77", "question": "Which schools served a grade span of Kindergarten to 9th grade in the county of Los Angeles and what is its Percent (%) Eligible FRPM (Ages 5-17)?", "cosine": 0.7256786218225735}



## synthetic:5 / snapshot 3

Input: And Los Angeles, only public schools?

Context: [{"role": "user", "content": "How many schools are in Alameda?"}]

Builder: {"action": "search", "question": "How many public schools are in Los Angeles?"}

Raw top candidate: {"id": "62", "question": "What is the total number of non-chartered schools in the county of Los Angeles with a percent (%) of eligible free meals for K-12 that is less than 0.18%?", "cosine": 0.6823609509787004}

Normalized top candidate: {"id": "77", "question": "Which schools served a grade span of Kindergarten to 9th grade in the county of Los Angeles and what is its Percent (%) Eligible FRPM (Ages 5-17)?", "cosine": 0.7256786218225735}



## synthetic:6 / snapshot 0

Input: Which

Context: [{"role": "user", "content": "Which molecules are carcinogenic?"}]

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:6 / snapshot 1

Input: Which molecules are carcinogenic

Context: [{"role": "user", "content": "Which molecules are carcinogenic?"}]

Builder: {"action": "search", "question": "Which molecules are carcinogenic?"}

Raw top candidate: {"id": "244", "question": "Is the molecule with the most double bonds carcinogenic? Show its label.", "cosine": 0.780784073926323}

Normalized top candidate: {"id": "244", "question": "Is the molecule with the most double bonds carcinogenic? Show its label.", "cosine": 0.7836907488632733}



## synthetic:6 / snapshot 2

Input: Which molecules are not carcinogenic?

Context: [{"role": "user", "content": "Which molecules are carcinogenic?"}]

Builder: {"action": "search", "question": "Which molecules are not carcinogenic?"}

Raw top candidate: {"id": "232", "question": "Please list top three molecules that have single bonds between two atoms and are not carcinogenic in alphabetical order.", "cosine": 0.7475642988240693}

Normalized top candidate: {"id": "232", "question": "Please list top three molecules that have single bonds between two atoms and are not carcinogenic in alphabetical order.", "cosine": 0.7475642988240693}



## synthetic:6 / snapshot 3

Input: Which molecules are not carcinogenic?

Context: [{"role": "user", "content": "Which molecules are carcinogenic?"}]

Builder: {"action": "search", "question": "Which molecules are not carcinogenic?"}

Raw top candidate: {"id": "232", "question": "Please list top three molecules that have single bonds between two atoms and are not carcinogenic in alphabetical order.", "cosine": 0.7475642988240693}

Normalized top candidate: {"id": "232", "question": "Please list top three molecules that have single bonds between two atoms and are not carcinogenic in alphabetical order.", "cosine": 0.7475642988240693}



## synthetic:7 / snapshot 0

Input: How

Context: [{"role": "user", "content": "How many patients are older than 60?"}]

Builder: {"gate": {"allow": false, "words": 1, "minimum_words": 3, "reason": "too-short"}, "status": "gated"}

Raw top candidate: null

Normalized top candidate: null



## synthetic:7 / snapshot 1

Input: How many patients are older than 60

Context: [{"role": "user", "content": "How many patients are older than 60?"}]

Builder: {"action": "search", "question": "How many patients are older than 60?"}

Raw top candidate: {"id": "1171", "question": "How many patients were under age when examined during the course of the four-year period from 1990 to 1993?", "cosine": 0.6649606857144599}

Normalized top candidate: {"id": "1171", "question": "How many patients were under age when examined during the course of the four-year period from 1990 to 1993?", "cosine": 0.7024264577601014}



## synthetic:7 / snapshot 2

Input: How many patients are older than 60? Sorry, younger than 60.

Context: [{"role": "user", "content": "How many patients are older than 60?"}]

Builder: {"action": "search", "question": "How many patients are younger than 60?"}

Raw top candidate: {"id": "1171", "question": "How many patients were under age when examined during the course of the four-year period from 1990 to 1993?", "cosine": 0.6917234206331602}

Normalized top candidate: {"id": "1171", "question": "How many patients were under age when examined during the course of the four-year period from 1990 to 1993?", "cosine": 0.7328206439707845}



## synthetic:7 / snapshot 3

Input: How many patients are older than 60? Sorry, younger than 60.

Context: [{"role": "user", "content": "How many patients are older than 60?"}]

Builder: {"action": "search", "question": "How many patients are younger than 60?"}

Raw top candidate: {"id": "1171", "question": "How many patients were under age when examined during the course of the four-year period from 1990 to 1993?", "cosine": 0.6917234206331602}

Normalized top candidate: {"id": "1171", "question": "How many patients were under age when examined during the course of the four-year period from 1990 to 1993?", "cosine": 0.7328206439707845}


