import networkx as nx
from networkx.readwrite import json_graph
import pickle
from random import choice,uniform,randint
import http_server
import json
import math
from itertools import combinations

class Optimize:

	G=None 
	F=None

	def prune(self,G):
		tbd=[]
		for n in Optimize.G.nodes():
			if sum(G.node[n]['alist'])==0 or sum(G.node[n]['ilist'])==0:
				tbd.append(n)
		for t in tbd:
			# print t
			G.remove_node(t)

	def remove_isolated(self,G):
		iso=[]
		for n in G.nodes():
			if G.degree(n)==0:
				iso.append(n)
		for i in iso:
			# print i
			G.remove_node(i)

	def makeallowed(self,allowedlist):
		A=open('allowed.txt')
		for w in A.readlines():
			allowedlist.append(w.strip())

	def filterallowed(self,allowedlist,income,age):
		tbd=[]
		for gene in Optimize.G.nodes():
			if str(gene) in allowedlist:
				if self.minimuminc(gene,income)==False or self.ageconst(gene,age)==False:
					tbd.append(str(gene))
		for t in tbd:
			allowedlist.remove(t)
		for s in allowedlist:
			print s


	def allowed(self,allowedlist,site):
		if str(site) in allowedlist:
			return True
		else:
			return False


	def C(self,n):
		return (Optimize.G.node[n]['reach']*4.5)+0.5;



	def D(self,i,j):
		return math.pow(10,(-1*Optimize.F.get(i).get(j)))



	# def U(n):
	# 	world=3000000000
	# 	return G.node[n]['reach']*(world/100)

	def I(self,n,size):
		Freq=Optimize.G.node[n]['pageviews']
		Freq=1 #NOT TAKING PAGEVIEWS PER USER INTO ACCOUNT
		return ((1000*self.budget)/(size*self.C(n)*Freq));


	def fitness(self,S):
	 	#S is a chromosome
	 	L=len(S)
	 	outsum=0
	 	overlap=0
	 	for i in range(1,L):
	 		insum=0
	 		for j in range(i+1,L):
	 			insum+= self.D(S[i],S[j])* min(self.I(S[i],L),self.I(S[j],L))
	 		outsum+=self.I(S[i],L)-insum
	 		overlap+=insum
	 	return (outsum,overlap)

	def fitnesspath(self,S): #PATH
		#S is a chromosome
		L=len(S)
		outsum=0
		overlap=0
		for i in range(0,L):
			allpaths=[]
			for j in range(i+1,L):
				path=nx.shortest_path(Optimize.G, source=S[i], target=S[j], weight='neglog')
				allpaths.append(path)
			
			delpaths=[]
			# print "All", allpaths
			
			for a, b in combinations(allpaths, 2):
				str1 = ''.join(a)
				str2 = ''.join(b)
				if str1 in str2:
					delpaths.append(b)
				elif str2 in str1:
					delpaths.append(a)

			for d in delpaths:
				if d in allpaths:
					allpaths.remove(d)

			# print "Del", delpaths

			insum=0
			for p in allpaths:
				l=len(p)
				insum+= self.D(p[0],p[l-1])* min(self.I(p[0],L),self.I(p[l-1],L))
			outsum+=self.I(S[i],L)-insum
			overlap+=insum
			# print "self.fitness ", outsum, " Overlap ", insum
		return (outsum,overlap)

	def weighted_choice(self,choices):
	   total = sum(w for c, w in choices)
	   r = uniform(0, total)
	   upto = 0
	   for c, w in choices:
		  if upto + w >= r:
			 return c
		  upto += w
	   assert False, "Error"


	def population_generate_random(self,allowedlist,P,size,income,age):
		#P is population of parents
		#size is size of each chromosome
		population=[]
		i=0
		while (i<P):
			chromosome=[]
			while (True):
				gene = choice(Optimize.G.nodes())#random node
				if not self.allowed(allowedlist,gene):
					continue
				# if minimuminc(gene,income)==False or ageconst(gene,age)==False:
				# 	continue
				if gene not in chromosome:
					chromosome.append(gene)
				if(len(chromosome)==size):
					break
			chromosome=sorted(chromosome, key= lambda node: Optimize.G.node[node]['reach']) 
			ch=tuple(chromosome)
			if ch not in population:
				population.append(ch)
				i=i+1

		for p in population:
			print p
		return population

	def population_generate_weighted(self,allowedlist,P,size,income,age):
		sortednodes=sorted(Optimize.G.nodes(), key= lambda node: Optimize.G.node[node]['reach']) 
		choices=[]
		for n in sortednodes:
			choices.append((n,Optimize.G.node[n]['reach']))

		population=[]
		i=0
		while (i<P):
			chromosome=[]
			while (True):
				gene = self.weighted_choice(choices)#random node
				if not self.allowed(allowedlist,gene):
					continue
				# if self.minimuminc(gene,income)==False or self.ageconst(gene,age)==False:
				# 	continue
				# print G.node[gene]['reach']
				if gene not in chromosome:
					chromosome.append(gene)
				if(len(chromosome)==size):
					break
			chromosome=sorted(chromosome, key= lambda node: Optimize.G.node[node]['reach']) 
			ch=tuple(chromosome)
			# ch.sort()
			if ch not in population:
				population.append(ch)
				i=i+1

		for p in population:
			print p
		return population

	def replace(self,l, X, Y):
	  for i,v in enumerate(l):
		 if v == X:
			l.pop(i)
			l.insert(i, Y)

	def pickparents(self,population):
		parents=[]
		choices=[]
		sortedpopulation=sorted(population, key= lambda ch: self.fitness(ch)[0]) 
		for ch in sortedpopulation:
			choices.append((ch,self.fitness(ch)[0]))

		i=0
		while(i<2):
			p=self.weighted_choice(choices)
			# if p not in parents:
			parents.append(p)
			i=i+1
		return parents

	def makechild(self,allowedlist,population, parents,income,age,mut):
		choices=[]
		child=[]
		size=len(parents[0])
		sortedparents=sorted(parents, key= lambda ch: self.fitness(ch)[0]) 
		for ch in sortedparents:
			choices.append((ch,self.fitness(ch)[0]))
		i=0
		while i<size:
			p=self.weighted_choice(choices)
			g=choice(p)
			r=randint(1,100)
			if mut==5:
				if r==1 or r==2 or r==3 or r==4 or r==5:
					g=choice(Optimize.G.nodes())
					if not self.allowed(allowedlist,g):
						continue
					# if minimuminc(g,income)==False or ageconst(g,age)==False:
					# 	continue
					print "Mutation"
			if mut==3:
				if r==1 or r==2 or r==3:
					g=choice(Optimize.G.nodes())
					if not self.allowed(allowedlist,g):
						continue
					# if minimuminc(g,income)==False or ageconst(g,age)==False:
					# 	continue
					print "Mutation"
			if mut==1:
				if r==1:
					g=choice(Optimize.G.nodes())
					if not self.allowed(allowedlist,g):
						continue
					# if minimuminc(g,income)==False or ageconst(g,age)==False:
					# 	continue
					print "Mutation"
			if g not in child:
				child.append(g)
				i=i+1

		child=tuple(child)

		FP0=self.fitness(parents[0])
		FP1=self.fitness(parents[1])
		FC=self.fitness(child)

		if child==parents[0] and child==parents[1]:
			return

		print parents[0] , " self.fitness: ", FP0[0], " Overlap: ", FP0[1]
		print parents[1] , " self.fitness: ", FP1[0], " Overlap: ", FP1[1]
		print child, " self.fitness: ", FC[0], " Overlap: ", FC[1]

		if min(FP0[0],FP1[0],FC[0])==FP0[0]:
			print "replaced: " ,parents[0]
			self.replace(population,parents[0],child)
		elif min(FP0[0],FP1[0],FC[0])==FP1[0]:
			print "replaced: " ,parents[1]
			self.replace(population,parents[1],child)
		else:
			print "No replacement"




	def minimuminc(self,site,inc):
		#inc can take values 0,30,60 or 100. 0 means no restriction
		# (0-30)(30-60)(60-100)(100+)
		if inc==0:
			return True
		if inc==30:
			if sum(Optimize.G.node[site]['ilist'][1:])>=300:
				return True
			else :
				return False
		if inc==60:
			if sum(Optimize.G.node[site]['ilist'][2:])>=200:
				return True
			else:
				return False
		if inc==100:
			if sum(Optimize.G.node[site]['ilist'][3])>=100:
				return True
			else:
				return False

	def ageconst(self,site,age):
		#age can take values 1)18-24 2)25-34 3)35-44 4)45-54 5)55-64 6)65+ 
		# 0 means no restriction
		if age==0:
			return True
		else:
			if Optimize.G.node[site]['alist'][age]>=100:
				return True
			else :
				return False



	def __init__(self, psize, csize,inc,age,mut,probselect,iteration,budget):
		self.budget=budget
		self.psize=psize
		self.csize=csize
		self.inc=inc
		self.age=age
		self.mut=mut
		self.probselect=probselect
		self.iteration=iteration

		Optimize.G = pickle.load(open('saved/graph300.txt'))
		self.prune(Optimize.G)
		self.remove_isolated(Optimize.G)
		for u,v,attr in Optimize.G.edges(data=True):
			Optimize.G.edge[u][v]['neglog']= -1*math.log10(Optimize.G.edge[u][v]['weight']) 
		Optimize.F=nx.floyd_warshall(Optimize.G, weight='neglog')




	def calculate(self):
		
		# d = json_graph.node_link_data(G) 
		# json.dump(d, open('force/force.json','w'))
		# http_server.load_url('force/force.html')
		allowedlist=[]
		self.makeallowed(allowedlist)
		self.filterallowed(allowedlist,self.inc,self.age)
		pop=[]
		if self.probselect == 0:
			print '\n\nRandom\n\n'
			pop=self.population_generate_random(allowedlist,self.psize,self.csize,self.inc,self.age)
		if self.probselect == 1:
			print '\n\nWeighted\n\n'
			pop = self.population_generate_weighted(allowedlist, self.psize,self.csize,self.inc,self.age)


		self.fitnesscurve=[]
		data=[]
		data.append(['Chromosome', 'self.fitness','Overlap'])
			

		for i in range(0,self.iteration): #ITERATIONS
			print "\n\n", i+1, "\n\n"
			par= self.pickparents(pop)
			self.makechild(allowedlist,pop,par,self.inc,self.age,self.mut)
			sortedpop=sorted(pop, key= lambda ch: self.fitness(ch)[0], reverse=True) 
			print "fittest: "
			F=self.fitness(sortedpop[0])
			print sortedpop[0], "self.fitness: ", F[0], "Overlap ", F[1]
			data.append([sortedpop[0], F[0], F[1]])
			
		return data

		
		
	
	
	
