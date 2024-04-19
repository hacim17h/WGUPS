# Name: Micah Calloway Student ID: 010663003
import re
import time
import datetime
from datetime import timedelta


START_OF_DAY = "8:00 AM"
END_OF_DAY = "5:00 PM"
TRUCK_AVERAGE_SPEED = 18
TRUCK_MAX_PACKAGES = 16


class Truck:
    """Stores truck information.

    The Truck class stores all data that is relevant to what is on or
    in the truck. The class is used reporting and status of the
    packages, loading the packages, and delivering them.
    """
    def __init__(self, name, average_speed, package_max,
                 location="HUB", location_key="HUBNone"):
        """Initializes base truck parameters."""
        self.name = name
        self.average_speed = average_speed
        self.package_list = HashTable(package_max)
        self.package_max = package_max
        self.package_count = 0
        self.location = location
        self.location_key = location_key
        self.current_time = convert_to_datetime(START_OF_DAY)
        self.remove_list = []
        self.miles_driven = 0

    def load_package(self, package, record):
        """Handles the loading of package data.

        If the truck doesn't have the max number of packages the
        method adds another one to the truck. It also handles all
        special packages ensuring groups can be added as well as making
        sure that packages that are delayed are not added.
        """
        note_type = None
        note_value = None
        if type(package) != list:
            if package.notes:
                note_type = notes_handler(package.notes)[0]
                note_value = notes_handler(package.notes)[1]
        if self.current_load() < self.package_max:
            # If it's a package group, add each package.
            if type(package) == list:
                if ((len(package) + self.current_load()) <
                        self.package_max):
                    self.remove_list.append(package)
                    for item in package:
                        item.status = f"En Route on {self.name}"
                        self.package_list.insert(item.id_, item)
                        record.insert(item.id_, item)
                        self.package_count += 1
            # Compares truck name to package and adds it if the same.
            elif note_type == "TruckRestriction":
                if self.name.lower() == note_value.lower():
                    self.remove_list.append(package)
                    package.status = f"En Route on {self.name}"
                    self.package_list.insert(package.id_, package)
                    record.insert(package.id_, package)
                    self.package_count += 1
            # Checks to see if the package is ready from flight delay.
            elif note_type == "FlightDelay":
                now = self.current_time
                delay_time = convert_to_datetime(note_value)
                if now >= delay_time:
                    self.remove_list.append(package)
                    package.status = f"En Route on {self.name}"
                    self.package_list.insert(package.id_, package)
                    record.insert(package.id_, package)
                    self.package_count += 1
            # Checks if the wrong address has been corrected yet.
            elif note_type == "WrongAddress":
                now = self.current_time
                address_time = convert_to_datetime(note_value[0])
                if now >= address_time:
                    self.remove_list.append(package)
                    package.address = note_value[1]
                    package.city = note_value[2]
                    package.state = note_value[3]
                    package.zip_ = note_value[4]
                    package.status = f"En Route on {self.name}"
                    self.package_list.insert(package.id_, package)
                    record.insert(package.id_, package)
                    self.package_count += 1
            # Otherwise if it isn't special, just add the package.
            else:
                self.remove_list.append(package)
                package.status = f"En Route on {self.name}"
                self.package_list.insert(package.id_, package)
                record.insert(package.id_, package)
                self.package_count += 1

    def load_truck(self, package_group, record):
        """Loads multiple packages at once.

        This method is used for loading up the truck from a list
        of packages. The packages that are eligible to be loaded
        are the removed from the list after the truck is full.
        """
        self.remove_list = []
        for package in package_group:
            if self.current_load() < self.package_max:
                self.load_package(package, record)
            else:
                break
        # Remove the packages that were loaded from the list.
        for package in self.remove_list:
            package_group.remove(package)

    def current_load(self):
        """Returns int of the number of packages on the truck."""
        return self.package_count

    def next_to_deliver(self, location_table):
        """Determines which package to deliver.

        The main method for determining which packages to deliver first.
        It goes through and picks the package with the earliest
        deadline. If all the packages have the same deadline it then
        selects the package that has the closest distance from the
        truck's location. It then returns the package to be delivered.
        """
        first_package = None
        is_first = True
        for elements in self.package_list.table:
            for i in range(len(elements)):
                if elements[i][1] and is_first:
                    first_package = elements[i][1]
                    is_first = False
        # Stores the data of the first package for initial comparison
        destination_key = first_package.address + first_package.zip_
        shortest_distance = (distance_apart(destination_key,
                                            self.location_key,
                                            location_table))
        id_of_closest = first_package.id_
        if first_package.deadline in "EOD":
            deadline_time = END_OF_DAY
        else:
            deadline_time = first_package.deadline
        earliest_deadline = convert_to_datetime(deadline_time)
        # Main loop that compares packages for distance and deadlines
        if self.package_count > 1:
            for elements in self.package_list.table:
                for i in range(len(elements)):
                    if elements[i][1]:
                        # If the deadline is sooner, add that package.
                        if elements[i][1].id_ != first_package.id_:
                            destination_key = (elements[i][1].address +
                                               elements[i][1].zip_)
                            new_distance = distance_apart(destination_key,
                                                          self.location_key,
                                                          location_table)
                            deadline_time = elements[i][1].deadline
                            new_deadline = convert_to_datetime(deadline_time)
                            if new_deadline < earliest_deadline:
                                earliest_deadline = new_deadline
                                shortest_distance = new_distance
                                id_of_closest = elements[i][1].id_
                            # If deadlines are the same, use distance.
                            elif new_deadline == earliest_deadline:
                                if new_distance < shortest_distance:
                                    earliest_deadline = new_deadline
                                    shortest_distance = new_distance
                                    id_of_closest = elements[i][1].id_
        next_to_deliver = self.package_list.retrieve(id_of_closest)
        return next_to_deliver

    def deliver_package(self, location_table, record):
        """Delivers the package that's determined next for delivery"""

        next_to_deliver = self.next_to_deliver(location_table)
        destination_key = next_to_deliver.address + next_to_deliver.zip_
        distance = distance_apart(destination_key, self.location_key,
                                  location_table)
        # Adjusts truck parameters to account for removing the package.
        self.package_count -= 1
        self.location = next_to_deliver.address
        self.location_key = next_to_deliver.address + next_to_deliver.zip_
        self.miles_driven += distance
        self.current_time = time_after_travel(distance,
                                              self.current_time,
                                              self.average_speed)
        # Update the package record and delivery status.
        next_to_deliver.status = (f"Delivered at "
                                  f"{self.current_time.strftime('%I:%M %p')} "
                                  f"by {self.name}")
        record.insert(next_to_deliver.id_, next_to_deliver)
        self.package_list.remove(next_to_deliver.id_)

    def time_after_deliver(self, location_table):
        """Estimates the time to travel to the package location.

        The method returns a datetime object of what time it will be
        after the package that is determined to be next would be
        delivered.
        """

        next_to_deliver = self.next_to_deliver(location_table)
        destination_key = next_to_deliver.address + next_to_deliver.zip_
        distance = distance_apart(destination_key, self.location_key,
                                  location_table)
        time_after_deliver = time_after_travel(distance, self.current_time,
                                               self.average_speed)
        return time_after_deliver

    def return_to_hub(self, location_table):
        """Sends truck back to HUB.

        The method returns the truck to the HUB and calculates the
        distance to travel there from the current location of the
        truck.
        """
        destination = "HUB"
        destination_key = "HUBNone"
        distance = distance_apart(destination_key, self.location_key,
                                  location_table)
        self.current_time = time_after_travel(distance, self.current_time,
                                              self.average_speed)
        self.location = destination
        self.location_key = destination_key
        self.miles_driven += distance

    def wait(self):
        """Passes time by 1 minute."""
        self.current_time = self.current_time + timedelta(minutes=1)

    def __str__(self):
        """Properly formats truck information in string form."""
        return f"{self.name} | {self.package_list.table} | {self.location}"


class Package:
    """Stores package components.

    The Package class stores all data that is relevant to the package.
    It is used for storage into other objects like the Truck.
    """
    def __init__(self, id_, address, city, state,
                 zip_, deadline, weight, notes=None,
                 status="In HUB"):
        """Initializes base package parameters."""
        self.id_ = id_
        self.address = address
        self.city = city
        self.state = state
        self.zip_ = zip_
        self.arrival_time = START_OF_DAY
        self.deadline = deadline
        self.weight = weight
        self.notes = notes
        self.status = status

    def __str__(self):
        """Properly formats package information in string form."""
        return ((f"{self.id_} | {self.address} | {self.city} | "
                 f"{self.state} | {self.zip_} | {self.deadline} | "
                 f"{self.weight} | {self.status} |"))


class Location:
    """Stores location components.

    The location class is used for storing distances to make distance
    comparisons easier. The index value keeps track of the order of
    the locations so that bidirectional distances can be more easily
    obtained.
    """
    def __init__(self, name, address, zip_, distances, index):
        """Initializes base location parameters."""
        self.name = name
        self.address = address
        self.zip_ = zip_
        self.distances = distances
        self.index = index

    def __str__(self):
        """Properly formats location information in string form."""
        return ((f"{self.name} | {self.address} | {self.zip_} | "
                 f"{self.distances} | {self.index}"))


class HashTable:
    """Creates hash table.

    The hash table has methods for insertion, removal, updating, and
    storing package data.
    """
    def __init__(self, size=10):
        """Initializes base hash table parameters."""
        self.size = size
        self.table = []
        for i in range(size):
            self.table.append([])

    def insert(self, key, value):
        """Inserts a key value pair into the hash table.

        A simple insert method that can store a package using the
        package id as a key. Package is already occupying the index
        of the list it will just append to that index via chaining.
        If the values of the keys are the same it will just update
        """
        index = key % self.size
        match = False
        match_index = 0

        if len(self.table[index]) > 0:
            for i in range(len(self.table[index])):
                if self.table[index][i][0] == key:
                    match = True
                    match_index = i
            if match:
                self.table[index][match_index] = [key, value]
            else:
                self.table[index].append([key, value])
        else:
            kv_pair = [key, value]
            self.table[index].append(kv_pair)

    def retrieve(self, key):
        """Returns package details.

        Takes a package id and returns the package details associated
        with that key if it exists.
        """
        index = key % self.size
        match = False
        match_index = 0

        if len(self.table[index]) > 0:
            for i in range(len(self.table[index])):
                if self.table[index][i][0] == key:
                    match = True
                    match_index = i
            if match:
                return self.table[index][match_index][1]
            else:
                return None
        else:
            return None

    def remove(self, key):
        """Removes a package.

        Takes a package id and removes the package with that key if
        it exists.
        """
        index = key % self.size
        match = False
        match_index = 0

        if len(self.table[index]) > 0:
            for i in range(len(self.table[index])):
                if self.table[index][i][0] == key:
                    match = True
                    match_index = i
            if match:
                self.table[index].remove(self.table[index][match_index])
            else:
                return None
        else:
            return None


def string_to_key(string):
    """Returns int key from string.

    Converts string to a numeric key to be used in the hashtable one
    letter at a time and then returns an integer.
    """
    key = ""
    for letter in string:
        if letter.lower().isalpha():
            if letter.lower() in "a":
                key += "1"
            elif letter.lower() in "b":
                key += "2"
            elif letter.lower() in "c":
                key += "3"
            elif letter.lower() in "d":
                key += "4"
            elif letter.lower() in "e":
                key += "5"
            elif letter.lower() in "f":
                key += "6"
            elif letter.lower() in "g":
                key += "7"
            elif letter.lower() in "h":
                key += "8"
            elif letter.lower() in "i":
                key += "9"
            elif letter.lower() in "j":
                key += "10"
            elif letter.lower() in "k":
                key += "11"
            elif letter.lower() in "l":
                key += "12"
            elif letter.lower() in "m":
                key += "13"
            elif letter.lower() in "n":
                key += "14"
            elif letter.lower() in "o":
                key += "15"
            elif letter.lower() in "p":
                key += "16"
            elif letter.lower() in "q":
                key += "17"
            elif letter.lower() in "r":
                key += "18"
            elif letter.lower() in "s":
                key += "19"
            elif letter.lower() in "t":
                key += "20"
            elif letter.lower() in "u":
                key += "21"
            elif letter.lower() in "v":
                key += "22"
            elif letter.lower() in "w":
                key += "23"
            elif letter.lower() in "x":
                key += "24"
            elif letter.lower() in "y":
                key += "25"
            elif letter.lower() in "z":
                key += "26"
        elif letter.lower().isdigit():
            key += letter
        else:
            key += "9"
    return int(key)


def load_package_data(filename):
    """Loads package data into a hash table.

    Opens the file and reads the package items one line at a time.
    After skipping the header, it parses each line and stores them into
    a package Object. It returns a hash table of package objects after the
    file is completed.
    """
    text_file = open(filename, 'rt')
    packages = text_file.readlines()
    packages.remove(packages[0])
    package_list = HashTable(len(packages))
    # The loop splits the data with regex and cleans extra characters.
    for package in packages:
        raw_data = re.split(r'(".+?"|[^,\n\t]+)', package)
        package_data = []
        for i in range(1, (len(raw_data) - 1)):
            if raw_data[i] != ",":
                package_data.append(raw_data[i])
        # Checks for special notes and adds them if they exist.
        if len(package_data) >= 8:
            package_list.insert(int(package_data[0]),
                                (Package(int(package_data[0]),
                                 package_data[1], package_data[2],
                                 package_data[3], package_data[4],
                                 package_data[5], float(package_data[6]),
                                 package_data[7].replace('"', ""))))
        else:
            package_list.insert(int(package_data[0]),
                                (Package(int(package_data[0]),
                                 package_data[1], package_data[2],
                                 package_data[3], package_data[4],
                                 package_data[5], float(package_data[6]))))

    return package_list


def load_location_data(filename):
    """Loads location data into a hash table.

    Opens the file and reads the location items one line at a time.
    After skipping the header, it parses each line and stores them into
    a location Object. It returns a hash table of location objects after the
    file is completed.
    """
    text_file = open(filename, 'rt')
    locations = text_file.readlines()
    locations.remove(locations[0])
    location_list = HashTable(len(locations))
    # The loops split the data with regex and cleans extra characters.
    for i in range(len(locations)):
        raw_data = re.split(r'(".+?"|[^,\n\t]+)', locations[i])
        location_data = []

        for j in range(1, (len(raw_data) - 1)):
            if raw_data[j] != ",":
                location_data.append(raw_data[j])

        name = location_data[0].replace('"', "")
        address = location_data[1].replace('"', "")
        address_parts = address.split("(")
        zip_ = None
        # Checks if it's the HUB and if not splits address and zip.
        if address_parts[0].lower() not in "hub":
            address = address_parts[0]
            address = address[slice(0, len(address) - 1)]
            zip_ = address_parts[1]
            zip_ = zip_[slice(0, len(zip_) - 1)]

        distances = []
        index = i
        # Creates a list of distances for location object.
        for j in range(2, len(location_data)):
            distances.append(float(location_data[j]))
        # Converts the location and the zip into a key for easy search
        # in the hashtable. Inserts it into the hashtable after.
        location_key = address + str(zip_)
        converted_key = string_to_key(location_key)
        location = Location(name, address, zip_, distances, index)
        location_list.insert(converted_key, location)

    return location_list


def notes_handler(notes):
    """Converts special notes into flags and data.

    Takes the special notes from packages and a list object that has
    the type of request followed by relevant values required by that
    request
    """
    if not notes:
        return None
    elif "can only be on" in notes.lower():
        notes_data = str(notes.lower()).split("can only be on ")
        note_type = "TruckRestriction"
        note_value = str(notes_data[1]).capitalize()
        return [note_type, note_value]
    elif "delayed on flight" in notes.lower():
        notes_data = str(notes.lower()).split(
            "delayed on flight---will not arrive to depot until ")
        note_type = "FlightDelay"
        note_value = str(notes_data[1]).upper()
        return [note_type, note_value]
    elif "wrong address listed" in notes.lower():
        note_type = "WrongAddress"
        note_value = ["10:20 AM", "410 S State St", "Salt Lake City",
                      "UT", "84111"]
        return [note_type, note_value]
    elif "must be delivered with" in notes.lower():
        notes_data = str(notes.lower()).split("must be delivered with ")
        note_type = "GroupRestriction"
        group_data = notes_data[slice(1, len(notes_data))]
        group_list = group_data[0].split(",")
        note_value = []
        for item in group_list:
            note_value.append(str(item).replace(" ", ""))
        return [note_type, note_value]


def compare_elements(list_1, list_2):
    """Compares package groups for common items.

    A simple helper function that takes 2 lists and compares the
    values. This will be used to compare package groups to see if they
    have any packages in common which would force them to be loaded
    onto the same truck.
    """
    match = False
    for item in list_1:
        for comparison in list_2:
            if item == comparison:
                match = True
    return match


def sort_packages(package_group):
    """Sorts packages with simple heuristics.

    This function goes through the hash table and retrieves the
    packages from it. It sorts all the special instruction packages
    and puts them at the top. It takes all packages that are in groups
    and puts them together in a package group. It returns a list of the
    sorted packages by earliest deadline of each group.
    """
    special_packages = []
    group_packages = []
    grouped_packages = []
    final_group = []
    delay_packages = []
    remaining_special = []
    package_list = []
    remaining_normal = []
    # Separates all packages with special notes.
    for elements in package_group.table:
        for j in range(len(elements)):
            if elements[j]:
                if elements[j][1].notes:
                    special_packages.append(elements[j][1])
            else:
                break
    # Separates out all the packages that must be in a group.
    for package in special_packages:
        if notes_handler(package.notes)[0] in "GroupRestriction":
            group_packages.append(package)

    # Goes through package groups to see if they have any packages in
    # common and puts them together ignoring duplicates if so.
    if len(group_packages) > 1:
        for i in range(len(group_packages)):
            package_set = set()
            for j in range(len(group_packages)):
                if group_packages[i].id_ != group_packages[j].id_:
                    notes_i = notes_handler(group_packages[i].notes)[1]
                    notes_j = notes_handler(group_packages[j].notes)[1]
                    if compare_elements(notes_i, notes_j):
                        for ids_ in notes_i:
                            package_set.add(ids_)
                        for ids_ in notes_j:
                            package_set.add(ids_)
                        package_set.add(group_packages[i].id_)
                        package_set.add(group_packages[j].id_)
            if package_set not in grouped_packages:
                grouped_packages.append(package_set)
            # If it had no matches it is a solo group so parse it solo.
            if not package_set:
                group_ids = notes_handler(group_packages[i].notes)[1]
                for ids_ in group_ids:
                    package_set.add(ids_)
                package_set.add(group_packages[i].id_)
                if package_set not in grouped_packages:
                    grouped_packages.append(package_set)
    # If it's just one package group, parse it solo.
    elif len(group_packages) == 1:
        package_set = set()
        group_ids = notes_handler(group_packages[0].notes)[1]
        for ids_ in group_ids:
            package_set.add(ids_)
        package_set.add(group_packages[0].id_)
        grouped_packages.append(package_set)

    # Removes smaller sets that are subsets of the larger sets.
    duplicate_group = []
    remove_list = []
    for package in grouped_packages:
        duplicate_group.append(package)
    for i in range(len(grouped_packages)):
        for j in range(len(grouped_packages)):
            if duplicate_group[i] != grouped_packages[j]:
                if duplicate_group[i].issubset(grouped_packages[j]):
                    remove_list.append(duplicate_group[i])
    for items in remove_list:
        grouped_packages.remove(items)

    # Retrieves all the actual package data in the groups and stores them.
    for groups in grouped_packages:
        temp_group = []
        for id_ in groups:
            temp_group.append(package_group.retrieve(int(id_)))
            sort_group_by_time(temp_group)
        final_group.append(temp_group)

    # Separates the delayed packages and any remaining special ones.
    for package in special_packages:
        if notes_handler(package.notes)[0] in "FlightDelay":
            package.arrival_time = notes_handler(package.notes)[1]
            delay_packages.append(package)
    for package in special_packages:
        if (notes_handler(package.notes)[0] not in "FlightDelay" and
                notes_handler(package.notes)[0] not in "GroupRestriction"):
            remaining_special.append(package)

    # Appends the special packages to the final package list.
    for groups in final_group:
        package_list.append(groups)
    sort_group_by_time(remaining_special)
    for packages in remaining_special:
        package_list.append(packages)
    sort_group_by_time(delay_packages)
    for packages in delay_packages:
        package_list.append(packages)

    # Goes through the hash table and removes the special packages.
    for groups in final_group:
        for package in groups:
            package_group.remove(int(package.id_))
    for package in remaining_special:
        package_group.remove((int(package.id_)))
    for package in delay_packages:
        package_group.remove((int(package.id_)))

    # Appends the rest of the packages in the hash table.
    for elements in package_group.table:
        for j in range(len(elements)):
            if elements[j]:
                remaining_normal.append(elements[j][1])
            else:
                break
    # Sorts and adds the remaining packages by the earliest deadline.
    sort_group_by_time(remaining_normal)
    for packages in remaining_normal:
        package_list.append(packages)

    return package_list


def sort_group_by_time(package_group):
    """Sorts list by deadline.

    A Helper function that takes a list and sorts packages with the
    lowest deadline time to the front of the list.
    """
    if len(package_group) > 1:
        for i in range(len(package_group) - 1):
            smallest = i
            for j in range(i + 1, len(package_group)):
                current_time = convert_to_datetime(
                    package_group[smallest].deadline)
                next_time = convert_to_datetime(
                    package_group[j].deadline)
                if next_time < current_time:
                    smallest = j
            if i is not smallest:
                temp = package_group[i]
                package_group[i] = package_group[smallest]
                package_group[smallest] = temp


def sort_group_by_id(package_group):
    """Sorts list by package id.

    A Helper function that takes a list and sorts packages with the
    lowest id number to the front of the list.
    """
    if len(package_group) > 1:
        for i in range(len(package_group) - 1):
            smallest = i
            for j in range(i + 1, len(package_group)):
                current_id = int(package_group[smallest].id_)
                next_id = int(package_group[j].id_)
                if next_id < current_id:
                    smallest = j
            if i is not smallest:
                temp = package_group[i]
                package_group[i] = package_group[smallest]
                package_group[smallest] = temp


def sort_by_earliest_truck(truck_group):
    """Sorts list by earliest truck.

    A Helper function that takes a list and sorts trucks with the
    lowest current time to the front of the list.
    """
    if len(truck_group) > 1:
        for i in range(len(truck_group) - 1):
            smallest = i
            for j in range(i + 1, len(truck_group)):
                current_time = truck_group[smallest].current_time
                next_time = truck_group[j].current_time
                if next_time < current_time:
                    smallest = j
            if i is not smallest:
                temp = truck_group[i]
                truck_group[i] = truck_group[smallest]
                truck_group[smallest] = temp


def distance_apart(current_key, destination_key, location_table):
    """Returns distance of two locations.

    Takes the string location key of the current location and the key
    of the destination location and returns the distance between the
    two locations.
    """
    current_location = location_table.retrieve(
        string_to_key(current_key))
    delivery_location = location_table.retrieve(
        string_to_key(destination_key))

    if current_location.index < delivery_location.index:
        distance = delivery_location.distances[current_location.index]
    else:
        distance = current_location.distances[delivery_location.index]

    return distance


def convert_to_datetime(time_):
    """Coverts time to a datetime object.

    A Helper function that takes a time in the format 00:00 PM/AM
    and then returns a datetime object with the corresponding time.
    It also converts the end of day text to a time based upon the end
    of day global constant"""
    if time_ in "EOD":
        temp_time = time.strptime(END_OF_DAY, '%I:%M %p')
    else:
        temp_time = time.strptime(time_, '%I:%M %p')
    temp_time_2 = datetime.time(temp_time.tm_hour, temp_time.tm_min)
    date_now = datetime.datetime.now()
    new_time = datetime.datetime.combine(date_now, temp_time_2)
    return new_time


def time_after_travel(distance, current_time, speed):
    """Returns time after traveling a distance.

    This function takes a distance and then based upon starting time
    of travel and the speed of travel it returns the time it would be
    after the travel.
    """
    minutes_passed = 60 * (distance / speed)
    time_passed = timedelta(minutes=minutes_passed)

    if type(current_time) is datetime.datetime:
        new_time = current_time + time_passed
        return new_time
    else:
        start_time = datetime.time(current_time.tm_hour, current_time.tm_min)
        date_now = datetime.datetime.now()
        new_date = datetime.datetime.combine(date_now, start_time)
        new_time = new_date + time_passed
        return new_time


def is_valid_time(input_):
    """Returns true if the input is in the form 00:00 PM/AM"""
    try:
        convert_to_datetime(input_)
        return True
    except ValueError:
        return False


def is_valid_option(input_):
    """Returns true if the input is in the range of the menu items"""
    valid_digits = [0, 1]
    try:
        if int(input_) in valid_digits:
            return True
        else:
            return False
    except ValueError:
        return False


def package_information(input_, trucks, package_group, location_table, record, selected_id=None):
    """Prints status of all packages at given time.

    The function takes all relevant information and runs a delivery
    projection up until the time specified and the prints the results
    including the package information of all packages and total miles
    driven"""
    time_ = input_
    stop_time = convert_to_datetime(time_)
    day_start = convert_to_datetime(START_OF_DAY)
    remaining_packages = 0
    truck_data = []
    valid_id = True

    # Checks to see if selected id exists and if it is valid
    if selected_id:
        if str(selected_id).isdigit():
            selected_id = int(selected_id)
        else:
            valid_id = False

    # Gets the number of packages in the package group.
    for package in package_group:
        if type(package) is list:
            for i in range(len(package)):
                remaining_packages += 1
        else:
            remaining_packages += 1
    # If the truck has packages, it will deliver them. If not, it will
    # goto the HUB to get more. Trucks who arrive soonest stock first.
    while remaining_packages > 0 and trucks and stop_time >= day_start:
        remove_list = []
        sort_by_earliest_truck(trucks)
        for truck in trucks:
            if truck.package_count == 0 and truck.location == "HUB":
                truck.load_truck(package_group, record)
                if truck.package_count == 0 and len(package_group) > 0:
                    if truck.current_time <= stop_time:
                        truck.wait()
                    else:
                        remove_list.append(truck)
                elif truck.package_count == 0 and len(package_group) == 0:
                    remove_list.append(truck)
            elif (truck.package_count == 0 and truck.location != "HUB" and
                  len(package_group) > 0):
                truck.return_to_hub(location_table)
                truck.load_truck(package_group, record)
            # If the truck is half full and near the HUB it restocks.
            elif (truck.package_count < int(truck.package_max / 2) and
                    (float(distance_apart(truck.location_key,
                                          "HUBNone",
                                          location_table)) < 3.0) and
                    (truck.location != "HUB") and len(package_group) > 0):
                truck.return_to_hub(location_table)
                truck.load_truck(package_group, record)
            elif truck.package_count > 0:
                delivery_time = truck.time_after_deliver(location_table)
                if delivery_time <= stop_time:
                    truck.deliver_package(location_table, record)
                    remaining_packages -= 1
                else:
                    remove_list.append(truck)
            else:
                remove_list.append(truck)
        # Removes any trucks that no longer can deliver packages.
        for truck in remove_list:
            truck_data.append(truck)
            trucks.remove(truck)

    # If enough time has passed, correct the wrong address.
    wrong_address = record.retrieve(9)
    note_value = notes_handler(wrong_address.notes)[1]
    if stop_time >= convert_to_datetime(note_value[0]):
        wrong_address.address = note_value[1]
        wrong_address.city = note_value[2]
        wrong_address.state = note_value[3]
        wrong_address.zip_ = note_value[4]
        record.insert(wrong_address.id_, wrong_address)
    if selected_id is None:
        # Display all the packages' status.
        print(f"-------------------------------------------\n"
              f"Status - All packages as of {stop_time.strftime('%I:%M %p')}\n"
              f"-------------------------------------------")
        record_list = []
        for items in record.table:
            for i in range(len(items)):
                record_list.append(items[i][1])
        sort_group_by_id(record_list)
        for packages in record_list:
            print(packages)

        # Displays the total miles.
        for truck in trucks:
            truck_data.append(truck)
        total_miles = 0
        for truck in truck_data:
            total_miles += truck.miles_driven
        print(f"-------------------------------------------\n"
              f"The total miles driven are: {total_miles:.1f}")
    else:
        # Display the specific package's status.
        if valid_id:
            fetched_package = record.retrieve(selected_id)
            if fetched_package:
                print(f"-------------------------------------------\n"
                      f"Status - Package {selected_id} as of "
                      f"{stop_time.strftime('%I:%M %p')}\n"
                      f"-------------------------------------------")
                print(record.retrieve(selected_id))
            else:
                print("The package requested does not exist.")
        else:
            print("The package ID requested is not valid.")


def main():
    """Generates the main menu.

    The main menu is displayed with input validation for the
    menu logic. It takes the file names of the data and once the user
    gives a valid input it generates package information for a specific
    time"""

    location_file = "CSVDistance.csv"
    package_file = "CSVPackage.csv"
    # The initial menu for selections.
    menu_option = input("-------------------------------------------\n"
                        "WGUPS Delivery Database\n"
                        "-------------------------------------------\n"
                        "1 - Check the status of any package\n"
                        "0 - Exit\n"
                        "Enter your selection: ")
    # Checks for valid input and then executes the menu choice.
    while not is_valid_option(menu_option):
        menu_option = input("Enter your selection: ")

    menu_option = int(menu_option)
    while menu_option != 0:
        if menu_option == 1:
            time_option = input("-------------------------------------------\n"
                                "Enter the time you wish to see package "
                                "information for or 0 to Exit\n"
                                "Enter your time (ex: 9:00 PM): ")

            if is_valid_time(time_option):
                package_option = input("Enter a package ID (Optional. "
                                       "Leave blank to see all): ")
                if package_option == "":
                    package_option = None
                package_table = load_package_data(package_file)
                package_record = load_package_data(package_file)
                location_table = load_location_data(location_file)
                truck_1 = Truck("Truck 1", TRUCK_AVERAGE_SPEED,
                                TRUCK_MAX_PACKAGES)
                truck_2 = Truck("Truck 2", TRUCK_AVERAGE_SPEED,
                                TRUCK_MAX_PACKAGES)
                truck_list = [truck_1, truck_2]
                package_group = sort_packages(package_table)
                package_information(time_option, truck_list, package_group,
                                    location_table, package_record,
                                    package_option)
            elif is_valid_option(time_option):
                menu_option = int(time_option)


if __name__ == '__main__':
    main()
