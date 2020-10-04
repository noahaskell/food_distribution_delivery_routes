# food_distribution_delivery_routes

A set of functions for taking a list of addresses, one of which is the origin, P of which are endpoints, and W of which are waypoints, and finding a set of routes.

The routes all start at the origin, where meal kits are picked up. The meal kits are delivered to the waypoints. The endpoints are the delivery drivers' addresses.

All waypoints must be visited, and the routes should minimize the total distance traveled for the drivers.

So, there are two major components to the problem:

1. Assign each waypoint to exactly one driver
2. Find the best route for each driver to visit all and only the waypoints assigned to her/him
