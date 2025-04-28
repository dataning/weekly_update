

I have multiple XML files to parse into a dataframe. They're organised by years so each charity would have multiple years XML files. The challenge is that each XML is a form-based content. While some fields are same, some are different depending on each charity what they would like to submit as some might submit more detail. The current strategy of parsing is to parse one XML into a wide dataframe and join them based on batch. And then join them together again after all the XML files parsing. There's another strategy to keep the XML parsing in long-form dataframe and join them together in the long form. To parse a partciular charity, you parse the name and the year and get everything related to that and then parse them into a wide data frame. My quesiton is that which one is more computation efficient, less error prone and easier to maintain and extract and filter. 


Hi Helen, thank you for reaching out! Can you expand on what you're asking? 