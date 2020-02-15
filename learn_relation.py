from __future__ import print_function


from owlready2 import *
from collections import defaultdict
import json
import owlready2
import random
import rdflib
from owlrl import *
from pyswip import Prolog, call, Functor


class individual:
    number = 0

    def __init__(self, link):
        individual.number = individual.number + 1
        self.__link = link

    def getFull(self):
        return self.__link

    def getName(self):

        if "#" in self.__link:
            s = self.__link.split('#')
            return s[1]
        else:
            s = self.__link.split('/')
            return s[len(s) - 1]

    def __eq__(self, other):
        if isinstance(other, individual):
            return self.getName() == other.getName()


class property:
    number = 0

    def __init__(self, link):
        property.number = property.number + 1
        self.__link = link
        self.__type = 'not set up'

    def getFull(self):
        return self.__link

    def setType(self, type):
        self.__type = type

    def getType(self):
        return self.__type

    def getName(self):
        s = self.__link.split('#')
        return s[1]

    def __eq__(self, other):
        if isinstance(other, property):
            return self.getName() == other.getName()


class tuple:
    def __init__(self, sub, pred, obj):
        self.__subject = sub
        self.__predicate = pred
        self.__object = obj

    def getInd(self):
        return self.__subject

    def getPred(self):
        return self.__predicate

    def getObj(self):
        return self.__object

    def __eq__(self, other):
        if isinstance(other, tuple):
            return self.__subject == other.__subject and self.__predicate == other.__predicate and self.__object == other.__object


class KB:
    def __init__(self, graph):
        self.__tuples = []
        self.__properties = []
        self.__individuals = []
        for s, p, o in graph:
            s = individual(s)
            p = property(p)
            o = individual(o)
            if p not in self.__properties:
                self.__properties.append(p)
            if s not in self.__individuals:
                self.__individuals.append(s)
            if o not in self.__individuals:
                self.__individuals.append(o)
            self.__tuples.append(tuple(s, p, o))

    def getProperties(self):
        return self.__properties

    def getIndividuals(self):
        return self.__individuals

    def getTuples(self):
        return self.__tuples

    def ObjectProperties(self):
        tuples = self.getTuples()
        ObjectProperties = []
        for e in tuples:
            o = e.getObj()
            if o.getName() == 'ObjectProperty':
                properties = self.getProperties()
                for p in properties:
                    i = e.getInd()
                    if p.getName() == i.getName():
                        ObjectProperties.append(p)
                        break
        return ObjectProperties


prolog = Prolog()
owlready2.JAVA_EXE = "C:/Program Files (x86)/Common Files/Oracle/Java/javapath/java.exe"
# onto_path.append("C:/Users/Angelo/Desktop/dataforproj/")
g = rdflib.Graph()
g.load("wine.rdf")
print("applicazione del reasoner...")
DeductiveClosure(RDFS_OWLRL_Semantics).expand(g)
Base = KB(g)
with open("Knowledge_base.pl", "w") as program:
    program.write(":- use_module('metagol').\n")
    nClause = input('inserisci il numero di clausole(MAX 10):')
    nClause = 10
    program.write("metagol: max_clauses(" + str(nClause) + ").\n")
    program.write("\n\n")
    ObjectProperties = Base.ObjectProperties()
    not_consideredP = []
    for e in ObjectProperties:
        if e.getName().lower() not in not_consideredP:
            program.write("body_pred(" + e.getName().lower() + "/2).\n")
    program.write("\n\n")
    Tuples = Base.getTuples()
    sameps = defaultdict(set)
    for e in Tuples:
        prop = e.getPred()
        if prop in ObjectProperties:
            indi = e.getInd()
            obj = e.getObj()
            sameps[prop.getName().lower()].add("(" + indi.getName().lower() + "," + obj.getName().lower() + ")")
    keysPred = sameps.keys()
    for e in keysPred:
        if e not in not_consideredP:
            for t in sameps[e]:
                program.write(e + t + ".\n")
    program.write("\n\n")
    # le
    metarule = [
        "metarule([P,Q], [P,A,B], [[Q,A,B]]).",  # identità,
        "metarule([P,Q],[P,A,B],[[Q,B,A]]).",  # inversa,
        "metarule([P,Q],[P,A,B],[[Q,C,A],[Q,C,B]]).",
        "metarule([P,Q],[P,A,B],[[Q,A,C],[Q,B,C]]).",
        "metarule(chain,[P,Q,R],[P,A,B],[[Q,A,C],[R,C,B]])."]  # chain
    for e in metarule:
        program.write(e + "\n")
    wines = set()
    white = set()
    red = set()
    relation = input("inserire la relazione da apprendere(arietà MAX 2)\n('esDim' per un esempio dimostrativo):")
    pos = []
    neg = []
    if relation == 'esDim':
        relation = 'samecolor'
        for t in sameps['hascolor']:
            thing = t.split(",")
            color = thing[1].replace(")", "")
            wine = thing[0].replace("(", "")
            wines.add(wine)
            if color == 'white':
                white.add(wine)
            if color == 'red':
                red.add(wine)
        for i in range(0, 60):
            w = random.sample(wines, 2)
            ex = relation + "(" + w[0] + "," + w[1] + ")"
            if w[0] in white and w[1] in white or w[0] in red and w[1] in red and w[0] != w[1]:
                if ex not in pos:
                    pos.append(ex)
            else:
                if ex not in neg:
                    neg.append(ex)
    else:
        ex = ''
        print("inserire gli esempi positivi('fine positivi' per inserire i negativi)")
        ex = input()
        while ex != 'fine positivi':
            pos.append(ex)
            ex = input()

        print("inserire gli esempi negativi('fine negativi' per terminare)")
        ex = input()
        while ex != 'fine negativi':
            neg.append(ex)
            ex = input()

    #seleziona dall'insieme degli esempi l'insieme di training
    tenp = len(pos) - len(pos) / 5
    tenp = int(tenp)  # arrotonda per difetto
    tenn = len(neg) - len(neg) / 5
    tenn = int(tenn)
    train_pos = random.sample(pos, tenp)  # seleziona il 90% degli esempi
    train_neg = random.sample(neg, tenn)

    with open("training_example.txt", "w") as tex:
        tex.write("positive example\n")
        for e in train_pos:
            tex.write(e + "\n")

        tex.write("\n\nnegative example\n")
        for e in train_neg:
            tex.write(e + "\n")

    program.write(":-\n")
    program.write("  Pos = [\n" + "		 " + ",\n		 ".join(pos) + "],\n")
    program.write("  Neg = [\n" + "		 " + ",\n		 ".join(neg) + "],\n")
    program.write("  learn(Pos,Neg).")

prolog = Prolog()
prolog.consult("metagol.pl")
prolog.consult("Knowledge_base.pl")
rules_list = []
with open('rules.pl', 'r') as f:  # chiude automaticamente il file
    for line in f:
        line = line.replace("\n", "")
        rules_list.append(line)
print(rules_list)
prolog.consult("rules.pl")  # acquisisce la regola
os.remove("rules.pl")
relation_name = relation
relation = Functor(relation, 2)
print('on positive example')

"""
seleziona dagli esempi totali gli esempi per il test set 
selezionando gli esempi che non sono stati utilizzati per il training
"""
for e in pos:
    if e not in train_pos:
        e = e.split("(")
        e = e[1].replace(")", "")
        e = e.split(",")
        print(relation_name + "(" + e[0] + "," + e[1] + ") ", end='')
        if call(relation(e[0], e[1])) == 1:
            print('true')
        else:
            print('false')
        # print(list(prolog.query(e + ".")))
print('on negative example')
for e in neg:
    if e not in train_neg:
        e = e.split("(")
        e = e[1].replace(")", "")
        e = e.split(",")
        print(relation_name + "(" + e[0] + "," + e[1] + ") ", end='')
        if call(relation(e[0], e[1])) == 1:
            print('true')
        else:
            print('false')
