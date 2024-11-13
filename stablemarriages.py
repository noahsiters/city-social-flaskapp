import random
import operator

def getStableMarriages(submissionObjs):
    males = []
    females = []
    matches = {}

    for sub in submissionObjs:
        if sub.getGender() == "Male":
            males.append(sub)
        elif sub.getGender() == "Female":
            females.append(sub)

    if len(males) != len(females):
        return False

    # get preference lists for each male and female
    # these lists are based on how similar their answers are, from most to least
    for male in males:
        male.setPreferenceList(generatePreferenceList(male, females))

    for female in females:
        female.setPreferenceList(generatePreferenceList(female, males))

    for male in males:
        matches[male] = ''

    males_free = list(males)

    random.shuffle(males)

    # while there are free men
    while len(males_free) > 0:
        for male in males:
            for female in male.getPreferenceList():
                if (male not in males_free):
                    break
                if female not in list(matches.values()):
                    matches[male] = female
                    males_free.remove(male)
                    break
                elif female in list(matches.values()):
                    current_suitor = list(matches.keys())[list(matches.values()).index(female)]
                    if getPercentageOfSimilarAnswers(male, female) > getPercentageOfSimilarAnswers(current_suitor, female):
                        matches[current_suitor] = ''
                        males_free.append(current_suitor)
                        matches[male] = female
                        males_free.remove(male)

    return matches

# this method generates a list of each suitors of the opposite gender from most similar answers to least similar answers
def generatePreferenceList(person, suitors):
    preferences = []
    preferencesDict = {}

    for suitor in suitors:
        preferencesDict[suitor] = getPercentageOfSimilarAnswers(person, suitor)

    preferences_sorted_desc = dict( sorted(preferencesDict.items(), key=operator.itemgetter(1), reverse=True))

    for key in preferences_sorted_desc:
        preferences.append(key)

    return preferences

# this method combines each persons answers to see how similar they are, and give it a percentage of similarity
def getPercentageOfSimilarAnswers(personA, personB):
        responsesA = personA.getResponses()
        responsesB = personB.getResponses()

        percentages = []

        for keyM in responsesA:
            for keyF in responsesB:
                if keyM == keyF: # only comparing IF the question is the same
                    # print(keyM + " : " + keyF)
                    if responsesA[keyM] == responsesB[keyF]: # if exact
                        percentages.append(1)
                    elif abs(responsesA[keyM] - responsesB[keyF]) == 1: # if 1 away
                        percentages.append(.75)
                    elif abs(responsesA[keyM] - responsesB[keyF]) == 2: # if 2 away
                        percentages.append(.50)
                    elif abs(responsesA[keyM] - responsesB[keyF]) == 3: # if 3 away
                        percentages.append(.25)
                    elif abs(responsesA[keyM] - responsesB[keyF]) == 4: # if opposite
                        percentages.append(0)

        return round((sum(percentages) / len(percentages)) * 100) # get the average percentage and move it one decimal