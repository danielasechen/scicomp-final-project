# Room Draw Optimizer 2 (w/filtering)
# Daniela Sechen
# Scientific Computing SPR'21

import pulp
import random

num_students = 100
students = list(range(1, num_students + 1))
num_rooms = 70
num_dorms = 9

# Dorm indices have the following order: 
#       (DW, Sontag, Linde, Case, Atwood, North, West, East, South)


# which[i] = (a, b) means dorm w/index i has rooms a THRU b
which_dorms_which_rooms = [(1, 8), (9, 17), (18, 27), (28, 35), (36, 42),
                             (43, 50), (51, 56), (57, 63), (64, 70)]

# The specific capacity of each room.
# room_capacities[i-1] = room i's capacity
room_capacities = [3] * num_rooms


# Randomly generate rankings and weights.
# dorm_rankings[i - 1] = student i's rank
# individ_weights[i - 1] = (d_i, r_i)
dorm_rankings = []
individ_weights = []
for i in range(num_students):
    ranks = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    random.shuffle(ranks)
    dorm_rankings.append(ranks)

    weight1 = random.randint(0, 10)
    weight_tuple = (weight1, 10-weight1)
    individ_weights.append(weight_tuple)


# Takes in a room number and uses which_dorms_which_rooms
# to determine which dorm the given room is in.
# Returning -1 indicates something bad happened (and this
# will probably break the rest of the code), but we should
# never hit this case.
def determine_dorm(room_num):
    for dorm_index in range(num_dorms):
        room_range = which_dorms_which_rooms[dorm_index]
        if room_range[0] - 1 <= room_num <= room_range[1] - 1:
            return dorm_index
    print("Uh oh!", room_num)
    return -1


# Return a filtered list of students for whom this room
# would not place the student in a dorm they dislike (rank >= 6).
def filter_students(room_num):
    filtered = []
    dorm = determine_dorm(room_num)
    for student in students:
        rank = dorm_rankings[student-1]
        if rank[dorm] <= 5:
            filtered.append(student)
    return filtered


# These are all possible roommate configurations.
# THE NUMBER IN FRONT indicates the assigned room.
possible_room_configs = []
for n in range(num_rooms):
    filtered_students = filter_students(n)
    possible_room_configs += [tuple([n]) + tuple(c) for c in \
                                pulp.allcombinations(filtered_students, 
                                                    room_capacities[n])]


# Takes in i, a student's number, and the dorm_given to student i
# and returns a happiness score based on student i's preferences.
def individ_dorm_happiness(i, room_given):
    dorm_given = determine_dorm(room_given)
    student_rank = dorm_rankings[i-1][dorm_given]
    return -1 * (num_dorms - student_rank + 2) * individ_weights[i-1][0]

# Calculates the total dorm happiness for a given room
# by running individ_dorm_happiness on each student in the room.
def dorm_happiness(config_given):
    total_happiness = 0
    for num in config_given[1:]:
        total_happiness += individ_dorm_happiness(num, config_given[0])
    return total_happiness


# Returns a happiness score for an entire room by summing up individ
# happiness for each student in the room
def roommate_happiness(config_given):
    total_happiness = 0
    for num in config_given[1:]:
        total_happiness += individ_roommate_happiness(num, config_given)
    return total_happiness

# Assumes all students prefer singles, then doubles, then triples.
# Returns a happiness score for student i based on individ weight
def individ_roommate_happiness(i, config_given):
    if len(config_given[1:]) == 1:
        return -10 * individ_weights[i-1][1]
    elif len(config_given[1:]) == 2:
        return -5 * individ_weights[i-1][1]
    else:
        return 0


# Create the variable to minimize
prob = pulp.LpProblem("RoomDrawOptimizer", pulp.LpMinimize)

# Create a binary variable to state that a room config is used.
# x is 1 when a room config is used, and 0 when it is not.
x = pulp.LpVariable.dicts('room', possible_room_configs, lowBound = 0,
                            upBound = 1, cat = pulp.LpInteger)


# Factoring in happiness costs
prob += pulp.lpSum(x[room] * (dorm_happiness(room) + \
                                roommate_happiness(room)) \
                    for room in possible_room_configs)

# A student must be placed in exactly one room
for student in students:
    prob += pulp.lpSum(x[room] for room in possible_room_configs
                        if student in room[1:]) == 1, "Must_place_%s"%student

# Each room can only be used once
for n in range(num_rooms):
    prob += pulp.lpSum(x[room] for room in possible_room_configs
                        if room[0] == n) <= 1, "Cant_reuse_room_%s"%n

# Solve!
prob.solve()

print("We've arranged the students into the following rooms:")
for room in possible_room_configs:
    if x[room].value() == 1.0:
        print("Room", room[0] + 1, "has student(s)", room[1:])
