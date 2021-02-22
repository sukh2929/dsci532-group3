## Reflection

### What we have implemented:

Our WHO Coronavirus Disease (COVID-19) [Dashboard](https://covid-19-mds-532-group3.herokuapp.com/) at this stage, has stayed loyal to what was suggested in our proposal and initial design from [milestone 1](https://github.com/UBC-MDS/dsci532-group3/releases/tag/0.1.0). We have considered feedback from TA and implemented accordingly in the current version of the application. As an example, we have decided to design the dashboard so that it has the Time/Location functionality (proposed as Time Period and Region tabs in the previous milestone) all in one place as described in the following lines.

The left-hand side of the dashboard is where all the necessary options for user(s) exploration exist. There is the Selection Mode which allows user(s) to choose the location of interest, which can be Country, Region or the whole World using radio buttons. An interesting feature of this option is that user(s) has the ability to choose multiple locations. Once an area is selected, the pertinent geographic location is highlighted on the right-hand side map. The map has a zoom functionality with which the user(s) can find the exact location of interest and even hover over to see the Country Code and Total number of Confirmed cases in that country . The user(s) can also select a desired Time Range or even choose to view the data in Absolute or Per Capita format.

The output data are represented in from of interactive line charts for total numbers of Confirmed, Deaths and Recovered cases per time and are placed at the bottom side of the dashboard page, where the user(s) can graphically track the trends of the COVID-19 statistics.

### Future improvements and additions:

We are and will be constantly striving to improve our application. In this vein, we are also determined to make the best use of the feedback that has been received on our progress and aim to implement certain features/improvements for the coming milestones of the project. Some of which are: 

- Adding versatility to the **Date range selection** option so that it allows for selection of monthly data as well and modify the line charts design accordingly. 

- Adding versatility to the **Selection Mode** option (World, Regions and Countries) so that it has enough space to show multiple selections (e.g. using a scrollbar feature).

- Adding a clickability option to the map. This feature helps user(s) with selecting the country of interest and bypass browsing a long list of countries. We tend to consider this as an optional feature to be added to our application in case time allows.

Just as the final note and making reference to a feedback from TA facing small delays in filtering functionality of our dashboard, we would like to acknowledge the fact that it is our understanding that although our dataset is considered as **Big** dataset, these technical glitches are typical of a low-memory server such as **Heroku** and will not be experienced with  better servers. 




