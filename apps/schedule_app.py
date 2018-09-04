"""
Script which manages the process of generating schedules, optimizing schedule times, and provides
a set of utility functions to interact with data. 
"""
import numpy as np
import random
from datetime import datetime, time, timedelta

class Schedule_Algorithm():
    """
    Class that provides functions and attributes to enable schedule generation for data provided

    Attributes:
        routes_stops (dict): Contains elements of type (dict) which represent each route, and contains
                             every stop for that route
        routes_schedules (dict): Contains elements of type (dict) which represent each trip generated by
                             the algorithm. Categorized by route and trip_id
        routes_schedules_finalized (dict): Contains elements of type (dict) which is used to store the
                             result of the finalized schedules for each route after optimization
    """
    ## Hour of day to start scheduling bus routes
    START_DAY_HOUR = 3
    routes_stops = {}
    routes_schedules = {}
    routes_schedules_finalized = {}

    def __init__(self, routes, buses, nodes, frequency, priority):
        self.routes = routes
        self.buses = buses
        self.nodes = nodes
        self.frequency = frequency
        self.priority = priority

    def arrangeRoutes(self):
        """
        Function which parses the stops associated with each route from self.routes, which contains
        all the waypoints for each route. Also determines which routes will be used to create schedule
        first, by initialising a routes_order variable
        """
        del self.priority[0]
        for priority in self.priority:
            ## Registers the stop_id and travel time from previous stop
            self.routes_stops[priority[0]] = [[route_point[4], route_point[5]] for route_point in self.routes
                                                  if route_point[0]==priority[0] and route_point[4]!=""]
            ## Add the route to the routes_schedules dict for later use by generateRouteSchedule()
            self.routes_schedules[priority[0]] = {}

        ## Append in order, the most important routes starting first that will be used to generate schedule
        priority_routes = self.priority.copy()
        self.routes_order = []
        priority_routes_loop = [int(priority[1]) for priority in priority_routes]
        for i in range(len(priority_routes)):
            priority_min_index = priority_routes_loop.index(min(priority_routes_loop))
            self.routes_order.append(self.priority[priority_min_index][0])
            priority_routes_loop[priority_min_index] = 20

    def generateSchedules(self, period="MF"):
        """
        For each route in the prioritized route order, call the generateRouteSchedule() function to
        generate a schedule for that route

        Args:
            period (str): The period of the week used to generate schedules
        """
        for route in self.routes_order:
            self.routes_schedules_finalized[route] = False
            self.generateRouteSchedule(route, period)
            print("Route: {} -- Trips: {}".format(route, len(self.routes_schedules[route])))
        print("Schedules created.")

    def evaluateNodeConnections(self, route):
        """
        For each node, print out the resulting performance variables using the currently generated
        schedule.

        Args:
            route (str): Route used to evaluate the wait time for each connection in that route
        """
        route_conn_time = 0
        for node in self.nodes:
            conn_times = node.evaluateConnectionTime(self.routes_schedules, route=route)
            for connection in conn_times:
                route_conn_time+=conn_times[connection]
        return route_conn_time                                                                                                                                                                                        

    def optimizeNodeConnections(self):
        """
        Function that optimizes the schedule, by optimizing performance variables for each node.
        Generates a schedule for each route, based on its priority, and shifts schedule times for each
        hour in order to accomodate for connecting routes.
        """
        route_node_numbers = self.calculateNodeNumber().copy()
        priority_routes = self.priority.copy()
        ## Get a dictionary with each index representing a route's priority, ranging from 1
        ## (highest priority) to 19 (lowest priority)
        prioritized_routes = self.getOrderedRoutes(priority_routes)

        for priority_category in prioritized_routes:
            for route in prioritized_routes[priority_category]:
                route_conn_time = self.evaluateNodeConnections(route)
                print("Route {} wait time: {}s".format(route, route_conn_time))
                self.minimizeRouteWaitTime(route)

    def minimizeRouteWaitTime(self, route):
        """
        Function which minimizes the wait time between connections for each separate hour of one day, and
        repeats the process untile very hour of the day is covered

        Args:
            route (str): Route and direction of route to be used for minimizing wait time for connections
        """
        current_hour = self.START_DAY_HOUR
        for i in range(24):
            if current_hour == 24:
                current_hour = 0

            for trip in self.routes_schedules[route]:
                trip_start_time = datetime.strptime(list(self.routes_schedules[route][trip].values())[0], "%H:%M:%S")
                print(trip_start_time.hour)

            current_hour+=1
        

    def generateRouteSchedule(self, route, period):
        """
        Function that generates the schedule for each route based on the route provided, and the frequency
        for each hour of the period provided. Calls generateTrip() in order to build the trip

        Args:
            route (str): Current route to be used for scheduling purposes
            period (str): Time period used to schedule (MF, S, Z)
        """
        current_route = route
        ## Fetches row with frequencies of current route
        current_route_frequency = self.frequency[[route[0] for route in self.frequency].index(current_route)]
        ## Only keeps the elements of frequency that match the schedule period requested (MF/S/Z)
        ## Find index of first and last hour of period
        header_start_index = self.frequency[0].index("{}00".format(period))
        header_fin_index = self.frequency[0].index("{}23".format(period))
        ## Fetch the frequencies of the current period
        current_route_frequency = current_route_frequency[header_start_index:(header_fin_index+1)]
        ## Shift list until first index points at first hour of day for trips
        current_route_frequency = current_route_frequency[self.START_DAY_HOUR:] + current_route_frequency[:self.START_DAY_HOUR]

        current_hour = self.START_DAY_HOUR
        count = 0
        trip_id_num = 0
        for current_hour_freq in current_route_frequency:
            if current_hour == 24:
                current_hour = 0
            freq_minutes = self.calculateFrequencyMinutes(int(current_hour_freq), 0)
            if freq_minutes is None:
                count+=1
                current_hour+=1
                continue
            for trip_minute in freq_minutes:
                ## Generate Trip ID with format: (27.10001) -- 0001 represents individual trip
                trip_id_num+=1
                trip_id = str("%s%04d"% (current_route, trip_id_num))
                ## With current trip ID, generate a trip, listing all the stop times for the route
                self.generateTrip(current_route, trip_id, current_hour, trip_minute)
            ## Break out of loop once after 24 hours past day start hour
            if count == 23:
                break
            count+=1
            current_hour+=1

    def generateTrip(self, current_route, trip_id, current_hour, trip_minute):
        """
        With the information provded, create a dictionary that is added to self.routes_schedules, and is
        used to contain the schedule information including each stop_id and stop time

        Args:
            current_route (str): Route used to schedule trip
            trip_id (str): Trip id to associate trip with
            current_hour (int): Hour used for start of trip
            trip_minute (int): Minute used for start of trip
        """
        self.routes_schedules[current_route][trip_id] = {}
        
        ## Determine time for first stop
        trip_time = datetime(2000, 1, 1, current_hour, trip_minute, 0)
        ## For each stop, use the travel time for next stop to calculate the trip_time
        for route_stop in self.routes_stops[current_route]:
            trip_time+= timedelta(seconds=int(route_stop[1]))
            self.routes_schedules[current_route][trip_id][route_stop[0]] = str(trip_time.time())

    def shiftHourlyTripTimes(self, trips, route, hour, seconds):
        """
        Function which shifts the trips belonging to a specific route, starting at a specific hour,
        by the number of seconds provided in the parameters. The purpose is to modify the schedule in
        such a way that it minimizes the wait time for each connection

        Args:
            trips (dict): Dictionary with elements of type (dict), representing each route, with elements of type (dict) representing each trip
            route (str): Route of the set of trips to shift
            hour (int): Hour of the day at which any trips of route beginning at that hour are shifted
            seconds (int): Number of seconds each trip will be shifted by in that hour
        """
        
        

    def shiftTripTime(self, trip, seconds):
        """
        Function to shift every stop time by the number of seconds provided. If seconds is negative,
        moves time back, positive moves time forward

        Args:
            trip (dict): Trip containing stop_id keys and time values
            seconds (str): Number of seconds by which to shift the trip times
            
        Returns:
            trip (dict): Trip where minutes are shifted by number of seconds provided
            
        """
        for stop in trip:
            timeStart = datetime.strptime(trip[stop], "%H:%M:%S")
            timeFinish = timeStart + timedelta(seconds=int(seconds))
            trip[stop] = str(timeFinish.time())
        return trip

    def calculateFrequencyMinutes(self, frequency, shift_min):
        """
        Function that generates a list of minutes in an hour, separated by a frequency and shifted by
        a provided number of minutes

        Args:
            frequency (int): Number of minutes every minute will be separated by
            shift_min (int): Number of minutes to shift every minute (if wanting to start at 04 mintues for eg)

        Returns:
            minutes (list): List containing minutes that are arranged according to arguments
            
        """
        if frequency > 60 or frequency < 1:
            return None
        
        minutes = []
        current_min = shift_min
        while current_min < 60:
            minutes.append(current_min)
            current_min+=frequency
        return minutes

    def calculateNodeNumber(self):
        """
        Function that calculates the number of nodes for each route, and returns a dict with the number
        of nodes

        Returns:
            route_node_numbers (dict): Dictionary listing the number of nodes for each route
        """
        route_node_numbers = {}
        for route in self.routes_stops:
            node_num = 0
            for stop in self.routes_stops[route]:
                for node in self.nodes:
                    if stop[0] in [e[1] for e in node.node_stops]:
                        node_num+=1
            route_node_numbers[route] = node_num
        return route_node_numbers

    def getOrderedRoutes(self, priority_routes):
        """
        Function which takes a dictionary of routes and corresponding priority, and returns a dictionary with each
        routes categorized by an index representing the priority of the routes provided

        Args:
            priority_routes (list): List containing elements of type (list) with first element that is the route, and second element its priority
        Returns:
            single_priority (dict): Dictionary containing index representing priority, and elements which are lists containing each route in that category
        
        """
        single_priority = {}
        priority_num = 1
        while True:
            single_priority[priority_num] = []
            ## Search every element in the routes' priority standing and collect all
            ## routes with the same highes priority
            for priority in priority_routes:
                if int(priority[1]) == priority_num and priority[0] not in single_priority[priority_num]:
                    single_priority[priority_num].append(priority[0])
            ## Completed one priority standing, and increment priority_num to search for lower priority
            priority_num+=1

            ## Set limit of priority to 20 and evaluate condition to break out of loop
            if priority_num == 20:
                break

        return single_priority
                        
