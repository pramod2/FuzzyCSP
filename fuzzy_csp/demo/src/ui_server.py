from flask import Flask
from fuzzy_csp.src.fuzzy_cs_problem import FuzzyCSProblem
from fuzzy_csp.src.fuzzy_cs_solution import FuzzyCSSolution
#from fuzzy_example_problem import FuzzyExampleProblem
from habit_parser import HabitParser
from habit_to_fcsp import HabitToFCSP
from demo_solution import DemoSolution
from flask_restful import reqparse
import json

####GLOBAL VARIABLES##########
data_path = '../data/'
brkfast_file = data_path + 'breakfast_log.txt'
ttl_file = data_path + 'time_to_last.txt'
pref_file = data_path + 'preferences.txt'
m = 5 #for m-best sols
done_startup = False

######END GLOBAL VARIABLES ########

####Instances required#####
habit_parser = None
habit_to_fcsp = None
demo_sol = None
###########################

def startup():
	print "RUNNING STARTUP.."
	global habit_parser
	global habit_to_fcsp
	global demo_sol
	if habit_parser == None: #we assume everything else is None
		print "Setting all variables.."
		habit_parser = HabitParser(brkfast_file, ttl_file, pref_file)
		habit_to_fcsp = HabitToFCSP(habit_parser)
		#print "Availability Problem.."
		avail_problem = habit_to_fcsp.get_availability_fcsp()
		#print "Desirability Problem.."
		desire_problem = habit_to_fcsp.get_desirability_fcsp()
		#print "Combined Problem.."
		combine_problem = habit_to_fcsp.get_combined_fcsp()
		demo_sol = DemoSolution(avail_problem, desire_problem, combine_problem)
		demo_sol.set_m(m)


startup()

app = Flask(__name__)
@app.route("/")
def hello():
	print "Came to hello!"
	combined = demo_sol.get_nth_best_combined_solution(1)
	desirability = demo_sol.get_nth_best_desirability_solution(1)
	
	availability = demo_sol.get_nth_best_availability_solution(1)
	#print "availability is", availability
	response_str = get_response_string(combined,desirability,availability)
	return response_str

@app.route("/sendNextPreference")
def sendMainPreference():
	parser = reqparse.RequestParser()
	parser.add_argument('attempt', type=int)
	args = parser.parse_args()
	print "Args are", args
	#print args = {'attempt': 1}
	attempt_num = args['attempt'] + 1

	combined = demo_sol.get_nth_best_combined_solution(attempt_num)
	desirability = demo_sol.get_nth_best_desirability_solution(1)
	
	availability = demo_sol.get_nth_best_availability_solution(1)

	response_str = get_response_string(combined,desirability,availability)
	return response_str


def get_stock_solution(sol):
	stock = []
	for item in sol:
		stock.append(habit_to_fcsp.get_availability_score(item))
	return stock

def get_response_string(combined, desirability, availability):
	response_dict = {}
	response_dict["combined"] = get_response_sol(combined)
	response_dict["desirability"] = get_response_sol(desirability)
	response_dict["availability"] = get_response_sol(availability)
	print "response_dict:", response_dict
	#return response_dict
	return json.dumps(response_dict)

#TODO: Doesn't make sense to hardcode variables
def get_response_sol(sol):
	response_sol = {"main":sol[0], "side":sol[1], "drink":sol[2]}
	return response_sol

if __name__ == "__main__":
	app.run()
