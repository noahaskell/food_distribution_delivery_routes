# Tikkun Farm food distribution program delivery routes

Originally, a set of functions for taking a list of addresses, one of which is the origin, P of which are endpoints, and W of which are waypoints, and finding a set of routes.

The routes all start at the single, shared origin, where meal kits are picked up. The meal kits are delivered to the waypoints. The endpoints are the delivery drivers' addresses.

All waypoints must be visited, and the routes should minimize the total distance traveled for the drivers.

So, there are two major components to the problem:

1. Assign each waypoint to exactly one driver
2. Find the best route for each driver to visit all and only the waypoints assigned to her/him

The code for a very flawed (and mostly poorly documented) version of this is in the find_routes directory.

More recently, I worked on writing better (and better documented) code to solve a simpler set of problems, namely:

1. read in lists of addresses from multiple sheets of a google spreadsheet.
2. use the google maps api to optimize the waypoints in each list (the first address is the origin, the last the destination)
3. make a google maps directions url for each route, write these to a file for the driver's to use
4. update the order of the addresses in the sheets so that they can be printed for the drivers

The code for this is in the optimize directory.
