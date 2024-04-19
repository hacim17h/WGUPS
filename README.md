# Project Overview
The WGUPS project was a challenging take on the traveling salesman problem. You must consider
several aspects like special package restrictions as well as package deadlines and other caveats.
There are several different locations, and it is spread across the city so accuracy in delivering the
packages despite the limitations is important. The algorithm also must be efficient enough to get
the job done in under 140 miles.

The algorithm used for the main logic in delivering the packages was the Greedy Algorithm. The
reason why I chose this is because it is simple to implement, and it made sense for this kind of
problem.

The main logic was that it simply first takes the package that has the earliest deadline and
delivers that. If they all have the same deadline it just delivers the package that is closest. After
each package is delivered it determines what package is closer based upon the truck’s current
location. Greedy Algorithms aren’t necessarily the most efficient, but it just picks the best option
at the time which is the core of my algorithm.
