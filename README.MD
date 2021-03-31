### Features

- Takes your notes and intelligently generate random Multiple-Choice sets formatted in a spreadsheet ready to upload straight to Kahoot. 

### Root-Trunk-Branch-Leaf Schema
- Notes should follow the Root-Trunk-Branch-Leaf schema. An example can be found in the source input folder.
- Roots are your overarching topics. When the script randomly generates questions, it first randomly selects a root, and then attempts to make a question, answer, and four multiple choices from within that Root.
- Trunks are your specific subtopic. If your Root was **Vehicles** your Trunks could be **Car, Train, Airplane**
- Branches are the defining characteristics of your Trunk. These should be generalizeable to all of the Trunks for the widest spread of useable questions, but they do not -need- to be. If your Trunk was **Car** your branches could be **Speed, Mass, Fuel**
- Leaves are the values for each branch. You can have multiple leaves by separating them with a comma. If **Car** was your trunk, and **Mass** is your branch, a leaf could be **2 tons**

### Question Generation
1. The code first randomly selects a Root and makes a set from all of the available Trunks.  
`roots = [Vehicles, Dinosaurs, France]`
`root = Vehicles`
2.  It randomly selects a Trunk from this set and then makes a set from all of the avaiable branches.
`Vehicles:[Car, Plane, Train]`
`trunk = Car`
3. It randomly selects a Branch, and its Leaf. If there are multiple leaves, it will select one randomly.
`Car:[Mass, Speed, Fuel]`
`branch = Mass`
4. Branch and Trunk are parsed together and become a potential question.
`trunk = Car    branch = Mass`
`Q1 = "Car Mass"`
5.  Your leaf is also a potential question.
`Q2 = "2 Tons"`
6. Coin toss decides which question remains as the question, the other becomes the answer. 
`coin = rand.choice[1,2] = 1`
`question, answer = Q1, Q2 if coin == 1 else Q2, Q1`
7. Code then loops through steps 2-5, references the coin toss, and discards the corresponding option.
`potQ1 = Train Speed potQ2 = 200mph`
`potA = potQ2 if coin ==1 else potQ1`
8. It compares the new potential answer against the original answer using Jaro-Winkler Similarity formula. If the potential answer scores 0.45 or less, or 1.0 (identical),  the answer is discarded and the cycle begins again. In this case, 200mph would be discarded, and the cycle starts again.
9. After four suitable multiple choices are found, the cycle begins at step 1.
10. This loop cycles until 100 questions are formed, since that is the limit imposed by Kahoot.
