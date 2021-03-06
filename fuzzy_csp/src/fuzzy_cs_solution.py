import itertools

class FuzzyCSSolution:
	def __init__(self, problem, joint_constraint_type = 'productive', upper_bound_type = "appropriateness", do_benchmark=False):
		self.problem = problem
		self.joint_constraint_type = joint_constraint_type
		self.search_tree = None
		self.upper_bound_type = upper_bound_type #can be "partial_joint_sat" or "appropriateness"
		self.do_benchmark = do_benchmark

	def set_joint_constraint_type(self, constraint_type):
		self.joint_constraint_type = constraint_type

	def get_joint_constraint_type(self):
		return self.joint_constraint_type


	def get_upper_bound_type(self):
		return self.upper_bound_type

	def set_upper_bound_type(self, upper_bound_type):
		self.upper_bound_type = upper_bound_type

	def set_do_benchmark(self,boolean):
		self.do_benchmark = boolean

	def get_do_benchmark(self):
		return self.do_benchmark

	#useful for backtracking, b&b, and similar
	#algorithms that require exploring tree
	def get_search_tree(self):
		#if function previously called, return the tree
		if self.search_tree != None:
			return self.search_tree

		tree = {}
		variables = self.problem.get_variables()
		for i in range(len(variables)):
			var = variables[i]
			values = self.problem.get_domain(var)
			if i == len(variables)-1: #last variable in the list
				children = []
			else:
				children = self.problem.get_domain(variables[i+1])

			#now put children for each value of this variable
			for value in values:
				tree[value] = children
		#set the search tree for this instance
		self.search_tree = tree
		return tree

######JOINT CONSTRAINT SATISFACTION #########

	def get_joint_satisfaction_degree(self, instantiation):
		#first check that instantiation is the right size
		return self.get_joint_constraint_satisfaction_degree(self.problem.constraints, instantiation)

	#for the new constraint model
	def get_joint_constraint_satisfaction_degree(self, constraints, instantiation):
		#TODO:first check that instantiation is the right size
		joint_satisfaction = 0.
		indiv_satisfaction_list = []
		for constraint in constraints:
			indiv_satisfaction = self.get_indiv_constraint_satisfaction_degree(constraint, instantiation)
			indiv_satisfaction_list.append(indiv_satisfaction)

		joint_satisfaction = self.get_joint_constraint_sat(indiv_satisfaction_list)

		return joint_satisfaction



	def get_indiv_constraint_satisfaction_degree(self,constraint, instantiation):
		#TODO:check that the instantiation is of right length
		if self.do_benchmark:
			FuzzyBenchmarkMetrics.num_constraint_checks += 1

		satisfaction = 0.
		for fuzzy_assignment in constraint.keys():
			satisfies = True
			for i in range(len(fuzzy_assignment)):
				if fuzzy_assignment[i] != instantiation[i]:
					if fuzzy_assignment[i] != None:
						satisfies = False
						break

			if satisfies == True:
				satisfaction = constraint[fuzzy_assignment]
				break
		return satisfaction


		for i in range(len(constraint)):
			if constraint[i] != instantiation[i]:
				if constraint[i] != None:
					return False
		return True


	def get_joint_constraint_sat(self, indiv_constraint_sats):
		indiv_satisfaction_list = indiv_constraint_sats
		if len(indiv_satisfaction_list) == 0:
			return 0.

		if self.joint_constraint_type == 'productive':
			#multiply each of them
			joint_satisfaction = 1.0
			for satisfaction in indiv_satisfaction_list:
				joint_satisfaction *= satisfaction
		elif self.joint_constraint_type == 'average':
			#print "avg joint sat.."
			joint_satisfaction = 0.0
			for satisfaction in indiv_satisfaction_list:
				joint_satisfaction += satisfaction
			joint_satisfaction = joint_satisfaction/float(len(indiv_satisfaction_list))
			#print "joint sat is", joint_satisfaction

		elif self.joint_constraint_type == 'min':
			joint_satisfaction = min(indiv_satisfaction_list)

		else:
			raise FCSSolutionException('Input the correct joint satisfaction type')

		return joint_satisfaction


	def get_partial_joint_satisfaction(self, partial_vars, partial_values):
		#create a dictionary for values and vars:
		partial_assignment_dict = {}
		for i in range(len(partial_vars)):
			variable = partial_vars[i]
			value = partial_values[i]
			partial_assignment_dict[variable] = value

		constraint_vars = []
		indiv_constraint_sats = []
		#first get all combinations of these partial_vars
		#print "partial vars is", partial_vars
		num_vars_per_constraint = self.problem.get_num_vars_per_constraint()
		#print "num_vars_per_constraint is", num_vars_per_constraint
		if len(partial_vars) < num_vars_per_constraint:
			#for each constraint, find the maximum one that contains these variables
			#TODO
			return 1.0
		else:
			all_constraint_vars = itertools.combinations(partial_vars, num_vars_per_constraint)

			for constraint_var in all_constraint_vars:
				var_list = list(constraint_var)
				value_list = [partial_assignment_dict[var] for var in var_list]
				#print "The var_list and value_list are", var_list, value_list
				constraint_sat = self.get_constraints_sat_with_fixed_vars(var_list, value_list)
				indiv_constraint_sats.append(constraint_sat)

		return self.get_joint_constraint_sat(indiv_constraint_sats)

####### END OF JOINT CONSTRAINT SATISFACTION ###################

######## START OF APPROPRIATENESS VALUE ###################


	#generator function to yield all instantiations
	def get_all_possible_instantiations(self,fixed_vars, fixed_values):
		#instantiations = []
		#TODO: Check if fixed_vars and fixed_values are same length

		#first fix the values of variables
		reduced_domains = self.problem.domains[:]
		for i in range(len(fixed_vars)):
			var = fixed_vars[i]
			value = fixed_values[i]
			var_ind = self.problem.variables.index(var)
			reduced_domains[var_ind] = [value]

		#print "the reduced domain is", reduced_domains
		#print "Reduced domains is", reduced_domains
		#now use the magic of itertools to get all possible instantiations
		for instance in itertools.product(*reduced_domains):
			#print "the instance being yielded is", instance
			yield instance
			#instantiations.append(instance)
		#return instantiations

	def get_constraints_with_variables(self, variables):
		reduced_constraints = []
		for constraint in self.problem.constraints:
			#if any of the variables have None as their value in the constraint
			constraint_assignment = constraint.keys()[0]; #an example assignment
			all_vars_satisfy = True
			for var in variables:
				var_ind = self.problem.variables.index(var)
				if constraint_assignment[var_ind] == None:
					all_vars_satisfy = False
					break
			if all_vars_satisfy:
				if self.do_benchmark:
					FuzzyBenchmarkMetrics.num_constraint_checks += 1
				reduced_constraints.append(constraint)
		return reduced_constraints


	#each fixed var must be same as num_vars_per_constraint
	#the values are as if the key to a constraint dictionary
	def get_constraints_sat_with_fixed_vars(self, variables, values):
		#first assert that the length of variables is same as num_vars_per_constraint
		assert len(variables) == self.problem.num_vars_per_constraint
		problem_variables = self.problem.variables

		#create constraint key
		constraint_key_list = [None]*len(problem_variables)
		for i in range(len(variables)):
			var = variables[i]
			value = values[i]
			problem_var_ind = problem_variables.index(var)
			constraint_key_list[problem_var_ind] = value
		constraint_key = tuple(constraint_key_list)


		constraints = self.get_constraints_with_variables(variables)
		if len(constraints) == 0:
			return 1
		#now find a specific constraint key and return the satisfaction
		return_sat = 0
		for constraint in constraints:
			if constraint_key in constraint:
				return_sat = constraint[constraint_key]
				break
		return return_sat

	#TODO: is there a better way?
	def get_appropriateness(self, variables, values):
		if len(variables) > self.problem.get_num_vars_per_constraint(): 
			all_constraints = self.problem.get_constraints()[:]
		else:
			all_constraints = self.get_constraints_with_variables(variables)
		#print "All instances for appropriateness are", all_instances
		#print "All constraints for appropriateness are", all_constraints
		if len(all_constraints) == 0: #these variables are unconstrained
			return 1

		best_joint_sat = 0
		for instance in self.get_all_possible_instantiations(variables, values):
			#print "current instance being checked is", instance
			joint_sat = self.get_joint_constraint_satisfaction_degree(all_constraints, instance)
			#print "joint sat for the instance is", joint_sat
			if joint_sat > best_joint_sat:
				best_joint_sat = joint_sat
		return best_joint_sat
	

	#fixed_vars is a dictionary of keys as variables and values as 
	#corresponding fixed values of those variables
	#ignore some values in difficulty and appr calculation
	def get_difficulty_and_appr(self, variable, fixed_vars, ignore_values):
		domain = self.problem.get_domain(variable)
		fixed_variables = fixed_vars.keys()
		appr_dict = {}
		difficulty = 0
		#print "variable, fixed_vars, ignore_values", variable, fixed_vars, ignore_values
		#print "domain is", domain
		for value in domain:
			if value in ignore_values:
				continue
			appr_variables = fixed_variables + [variable]
			appr_values = []
			for fixed_var in fixed_variables:
				fixed_val = fixed_vars[fixed_var]
				appr_values.append(fixed_val)
			appr_values = appr_values + [value]

			appr = self.get_appropriateness(appr_variables, appr_values)
			appr_dict[value] = appr
			difficulty += appr
		return difficulty, appr_dict




	def heuristic_search(self):
		variables = self.problem.variables
		fixed_vars = {}
		assigned_vars = []
		backtracked_assignments = {}
		
		while len(fixed_vars)<len(variables):
			best_appr_dict = None
			least_diff = float('inf')
			var_to_set = None
			backtracking = False
			for variable in variables:
				if variable not in fixed_vars:
					ignore_values = []
					#print "backtracked assignments are", backtracked_assignments
					if variable in backtracked_assignments:
						ignore_values = backtracked_assignments[variable]
					#print "The variable, fixed vars, and ignore_values are", variable, fixed_vars, ignore_values
					difficulty, appr_dict = self.get_difficulty_and_appr(variable, fixed_vars, ignore_values)

					#print "difficulty_and_appr of variables",variable,"with fixed vars:", fixed_vars, "are:\n", difficulty, appr_dict
					if appr_dict and difficulty>0 and difficulty<least_diff:
						least_diff = difficulty
						best_appr_dict = appr_dict
						var_to_set = variable
			#if none of the next variable assignment is consistent with the current one
			#difficulty = 0 for all, so backtrack
			if least_diff == float('inf') or least_diff == 0: 
				#this means appropriateness is 0 for all values, i.e. constraints violated
				#i.e. we need backtracking, i.e. go to previous variable, and consider values other than the one. 
				# in the fixed_vars.
				backtracking = True
				#pop the latest variable from assigned and 
				#fixed_vars and do the same thing with reduced domain
				#also need to see if the domain has been reduced to empty set
				if len(assigned_vars) >0:
					latest_variable = assigned_vars.pop()
				else:
					print "No feasible solution exists"
					return None
					#raise FCSSolutionException("No feasible solution exists!!")
				assigned_val = fixed_vars[latest_variable]

				#add to backtracked assignments
				if latest_variable in backtracked_assignments:
					backtracked_assignments[latest_variable].append(assigned_val) 
				else:
					backtracked_assignments[latest_variable] = [assigned_val]
				del fixed_vars[latest_variable]
				
				#break

			if backtracking: #if backtracking, don't continue with setting up assignments
				print "backtracking due to inconsistency of",latest_variable, assigned_val
				#print "fixed vars are:", fixed_vars
				continue
			if best_appr_dict == None:
				raise FCSSolutionException('Code should not come here. Look at heuristic_search function.')

			#now instantiate the var_to_set
			appr_var_assignment= self.get_best_appr_var_assignment(best_appr_dict)
			if appr_var_assignment:
				fixed_vars[var_to_set] = appr_var_assignment
				assigned_vars.append(var_to_set)

			if self.do_benchmark:
				FuzzyBenchmarkMetrics.num_var_assignments += 1
			#print "var to set is", var_to_set
			#print "best_appr_dict is", best_appr_dict		
			#print "least difficulty is", least_diff			
			#print "fixed_vars are", fixed_vars			
			#print "assigned vars are", assigned_vars
		#make sure it's a full assignment
		assert len(fixed_vars) == len(self.problem.get_variables())
		#make sure none of the assigned values is None
		assert None not in fixed_vars.values()

		return fixed_vars

	def get_best_appr_var_assignment(self, best_appr_dict):
		max_appr = 0
		best_assignment = None
		for assignment in best_appr_dict:
			if best_appr_dict[assignment] > max_appr:
				max_appr = best_appr_dict[assignment]
				best_assignment = assignment
		return best_assignment





	def get_heuristic_solution(self):
		solution = self.heuristic_search()
		if not solution:
			return False
		instance = [None] * len(solution)

		for i in range(len(self.problem.get_variables())):
			variable = self.problem.get_variables()[i]
			instance[i] = solution[variable]

		#make sure there is no None assigned for any variable
		assert None not in instance
		instance = tuple(instance)

		return instance



	#b&b based on dfs and backtracking. Uses appropriateness value 
	#as the upper bound while bounding. returns the best solution
	def get_branch_and_bound_solution(self):
		graph = self.get_search_tree()
		root_variable = self.problem.get_variables()[0]
		root_values = self.problem.get_domain(root_variable)		

		feasible_solution = self.get_a_feasible_solution_backtracking()
		if not feasible_solution:
			print "No feasible solution exists."
			return None
		best_joint_sat = self.get_joint_satisfaction_degree(feasible_solution)

		best_solution = feasible_solution
		#create initial stack with the root variables
		stack = []
		for root_val in root_values:
			stack.append((root_val, [root_val]))

		while stack:
			#print "bnb stack is", stack
			(vertex, path) = stack.pop(0)
			if self.do_benchmark:
				FuzzyBenchmarkMetrics.num_var_assignments += 1
			#print "bnb vertex is", vertex
			#print "bnb path is", path
			for next in graph[vertex]:
				#check if the path with next variable has better joint_sat than current max
				next_partial_assignment = path+[next];
				partial_vars = self.problem.get_variables()[:len(next_partial_assignment)]
				#upper bound for branch_and_bound
				upper_bound = 1.0
				if self.get_upper_bound_type() == "appropriateness":
					upper_bound = self.get_appropriateness(partial_vars, next_partial_assignment)
				elif self.get_upper_bound_type() == "partial_joint_sat":
					upper_bound = self.get_partial_joint_satisfaction(partial_vars, next_partial_assignment)
				
				if upper_bound < best_joint_sat:
					#prune/don't go to this branch
					continue
					
				if graph[next] == []: # next vertex is the leaf
					instance = tuple(path + [next])
					#print "Instance is", instance
					joint_sat = self.get_joint_satisfaction_degree(instance)
					if joint_sat > best_joint_sat:
						best_joint_sat = joint_sat
					best_solution = instance
					continue
				else:
					stack = [(next, path+[next])] + stack		

		return best_solution



	#gives all alpha solutions using branch and bound pruning
	def get_alpha_solutions_branch_n_bound(self, alpha):
		graph = self.get_search_tree()
		root_variable = self.problem.get_variables()[0]
		root_values = self.problem.get_domain(root_variable)		

		lower_bound = alpha
		#create initial stack with the root variables
		stack = []
		for root_val in root_values:
			stack.append((root_val, [root_val]))

		while stack:
			#print "bnb stack is", stack
			(vertex, path) = stack.pop(0)
			if self.do_benchmark:
				FuzzyBenchmarkMetrics.num_var_assignments += 1
			#print "bnb vertex is", vertex
			#print "bnb path is", path
			for next in graph[vertex]:
				#check if the path with next variable has better joint_sat than current max
				next_partial_assignment = path+[next];
				partial_vars = self.problem.get_variables()[:len(next_partial_assignment)]
				#upper bound for branch_and_bound
				upper_bound = 1.0
				if self.get_upper_bound_type() == "appropriateness":
					upper_bound = self.get_appropriateness(partial_vars, next_partial_assignment)
				elif self.get_upper_bound_type() == "partial_joint_sat":
					upper_bound = self.get_partial_joint_satisfaction(partial_vars, next_partial_assignment)
				
				if upper_bound < lower_bound:
					#prune/don't go to this branch
					continue
					
				if graph[next] == []: # next vertex is the leaf
					instance = tuple(path + [next])
					#print "Instance is", instance
					joint_sat = self.get_joint_satisfaction_degree(instance)
					if joint_sat >= alpha:
						yield tuple(path + [next])
				else:
					stack = [(next, path+[next])] + stack		
		

	#done with dfs and backtracking. gets all solutions 
	#with joint satisfaction more than alpha
	def get_alpha_solutions_backtracking(self, alpha):
		#print "Called alpha solution.."
		graph = self.get_search_tree()
		#print "Graph is", graph
		root_variable = self.problem.get_variables()[0]
		root_values = self.problem.get_domain(root_variable)		

		#create initial stack with the root variables
		stack = []
		for root_val in root_values:
			to_add = (root_val, [root_val])
			#stack = [to_add]+stack
			stack.append(to_add)

		while stack:
			#print "stack is", stack
			(vertex, path) = stack.pop(0)
			if self.do_benchmark:
				FuzzyBenchmarkMetrics.num_var_assignments += 1
			#print "vertex is", vertex
			#print "path is", path
			for next in graph[vertex]:

				if graph[next] == []: # next vertex is the leaf
					instance = tuple(path + [next])
					joint_sat = self.get_joint_satisfaction_degree(instance)
					if joint_sat >= alpha:
						yield instance
				else:
					stack = [(next, path+[next])] + stack


	#uses backtracking to find all feasible solutions
	def get_all_feasible_solutions_backtracking(self):
		import sys
		#epsilon is the "smallest constant" greater than zero
		return self.get_alpha_solutions_backtracking(sys.float_info.epsilon)

	#uses backtracking to find a feasible solution
	def get_a_feasible_solution_backtracking(self):
		import sys
		for solution in self.get_alpha_solutions_backtracking(sys.float_info.epsilon):
			return solution
	#def get_m_best_solutions(self):

	#backtracking to find alpha solution by default
	def get_an_alpha_solution_backtracking(self,alpha):
		for solution in self.get_alpha_solutions_backtracking(alpha):
			return solution

	#an alpha solution with branch and bound
	def get_an_alpha_solution_branch_n_bound(self, alpha):
		for solution in self.get_alpha_solutions_branch_n_bound(alpha):
			return solution

	#a function for returning m-best solutions
	def get_m_best_solutions_backtracking(self, m):
		m_soln_dict = {} #will stop growing when it reaches m
		import sys
		for solution in self.get_alpha_solutions_backtracking(sys.float_info.epsilon):
			sat_degree = self.get_joint_satisfaction_degree(solution)
			m_soln_dict[solution] = sat_degree
		degree_sorted_solns = sorted(m_soln_dict, key=lambda k: m_soln_dict[k])
		if m<=len(degree_sorted_solns):
			return degree_sorted_solns[(len(degree_sorted_solns)-m):]
		else:
			return degree_sorted_solns


	def get_m_best_solutions_branch_n_bound(self,m):
		graph = self.get_search_tree()
		root_variable = self.problem.get_variables()[0]
		root_values = self.problem.get_domain(root_variable)		

		lower_bound = 0

		m_solutions = []
		m_sat_degrees = []
		current_min_sat = float('inf')
		#create initial stack with the root variables
		stack = []
		for root_val in root_values:
			stack.append((root_val, [root_val]))

		while stack:
			#print "bnb stack is", stack
			(vertex, path) = stack.pop(0)
			if self.do_benchmark:
				FuzzyBenchmarkMetrics.num_var_assignments += 1
			#print "bnb vertex is", vertex
			#print "bnb path is", path
			for next in graph[vertex]:
				#check if the path with next variable has better joint_sat than current max
				next_partial_assignment = path+[next];
				partial_vars = self.problem.get_variables()[:len(next_partial_assignment)]
				#upper bound for branch_and_bound
				upper_bound = 1.0
				if self.get_upper_bound_type() == "appropriateness":
					upper_bound = self.get_appropriateness(partial_vars, next_partial_assignment)
				elif self.get_upper_bound_type() == "partial_joint_sat":
					upper_bound = self.get_partial_joint_satisfaction(partial_vars, next_partial_assignment)
				
				if upper_bound <= lower_bound:
					#prune/don't go to this branch
					continue
					
				if graph[next] == []: # next vertex is the leaf
					instance = tuple(path + [next])
					#print "Instance is", instance
					joint_sat = self.get_joint_satisfaction_degree(instance)

					if len(m_solutions) < m:
						m_solutions.append(instance)
						m_sat_degrees.append(joint_sat)
						if (len(m_solutions) == m): #after appending above
							current_min_sat = min(m_sat_degrees)
							lower_bound = current_min_sat
					else:
						if joint_sat > current_min_sat:
							min_index = m_sat_degrees.index(current_min_sat)
							m_solutions[min_index] = instance
							m_sat_degrees[min_index] = joint_sat
							current_min_sat = min(m_sat_degrees)
							lower_bound = current_min_sat
				else:
					stack = [(next, path+[next])] + stack
		sorted_sols_with_sats = sorted(zip(m_sat_degrees, m_solutions))
		#print "sorted zip is", sorted_sols_with_sats
		m_sols_ascending = [sol for (sat, sol) in sorted_sols_with_sats]
		#print "sorted sols are", m_sols_ascending
		return m_sols_ascending



	def get_m_best_fixed_solutions_branch_n_bound(self,m, want_items, no_want_items):
		graph = self.get_search_tree()
		root_variable = self.problem.get_variables()[0]
		root_values = self.problem.get_domain(root_variable)		

		lower_bound = 0

		m_solutions = []
		m_sat_degrees = []
		current_min_sat = float('inf')
		#create initial stack with the root variables
		stack = []
		for root_val in root_values:
			stack.append((root_val, [root_val]))

		while stack:
			#print "bnb stack is", stack
			(vertex, path) = stack.pop(0)
			if self.do_benchmark:
				FuzzyBenchmarkMetrics.num_var_assignments += 1
			#print "bnb vertex is", vertex
			#print "bnb path is", path
			for next in graph[vertex]:
				if next in no_want_items or vertex in no_want_items:
					continue
				#check if the path with next variable has better joint_sat than current max
				next_partial_assignment = path+[next];
				partial_vars = self.problem.get_variables()[:len(next_partial_assignment)]
				#upper bound for branch_and_bound
				upper_bound = 1.0
				if self.get_upper_bound_type() == "appropriateness":
					upper_bound = self.get_appropriateness(partial_vars, next_partial_assignment)
				elif self.get_upper_bound_type() == "partial_joint_sat":
					upper_bound = self.get_partial_joint_satisfaction(partial_vars, next_partial_assignment)
				
				if upper_bound <= lower_bound:
					#prune/don't go to this branch
					continue
					
				if graph[next] == []: # next vertex is the leaf
					instance = tuple(path + [next])
					
					#check if solution has items wanted (it's an OR)
					# i.e. if a solution contains any of the wanted items,
					# it's a valid solution. 
					sol_is_wanted = False
					if len(want_items) == 0:
						sol_is_wanted = True
					for item in want_items:
						if item in instance:
							sol_is_wanted = True
							break

					if not sol_is_wanted:
						continue
					#print "Instance is", instance
					joint_sat = self.get_joint_satisfaction_degree(instance)

					if len(m_solutions) < m:
						m_solutions.append(instance)
						m_sat_degrees.append(joint_sat)
						if (len(m_solutions) == m): #after appending above
							current_min_sat = min(m_sat_degrees)
							lower_bound = current_min_sat
					else:
						if joint_sat > current_min_sat:
							min_index = m_sat_degrees.index(current_min_sat)
							m_solutions[min_index] = instance
							m_sat_degrees[min_index] = joint_sat
							current_min_sat = min(m_sat_degrees)
							lower_bound = current_min_sat
				else:
					stack = [(next, path+[next])] + stack
		sorted_sols_with_sats = sorted(zip(m_sat_degrees, m_solutions))
		#print "sorted zip is", sorted_sols_with_sats
		m_sols_ascending = [sol for (sat, sol) in sorted_sols_with_sats]
		#print "sorted sols are", m_sols_ascending
		return m_sols_ascending



#have to put here because putting inside fuzzy_benchmark_test caused circular dependency
#during import
class FuzzyBenchmarkMetrics():
	num_constraint_checks = 0
	num_var_assignments = 0

class FCSSolutionException(Exception):
    def __init__(self, msg):
        self.msg = msg
