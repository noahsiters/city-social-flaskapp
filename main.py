from flask import Flask
from flask import render_template
from flask import request
from flask import redirect

import os
import dotenv # type: ignore
import json
import submission
import stablemarriages

from jotform import JotformAPIClient

app = Flask(__name__)

# index page route
@app.route("/")
@app.route("/<key>")
def index(key=None):
    return render_template("index.html", key=key)

# form action
@app.route("/f_dataInput", methods=["POST"])
def dataInput():
    # get form data
    key = request.form["apikey"]
    formId = request.form["submissionId"]

    # TODO for testing purposes
    # key = 'cf7568f8711ff6cdaa95d591bf0c3108'
    # formId = '241778563027160'

    # check for valid user
    try:
        jotform = JotformAPIClient(key)
        user = jotform.get_user()
    except:
        return redirect("/BadKey")
    
    # check if id was a SINGLE FORM id or a LIST of submission ids
    if "," in formId:
        submissionObjs = gatherSubmissionsFromList(key, formId)
    else:
        submissionObjs = gatherSubmissionsFromForm(key, formId)

    if submissionObjs == False:
        return redirect("/BadForm")
        
    # returnString = "<a href='/'>back</a>\n<ul>\n"
    # try:
    #     for sub in formattedSubmissions:
    #         returnString += "<li>" + sub + "</li>\n"
    # except:
    #     return redirect("/BadForm")
    # returnString += "</ul>"

    # return returnString

    # return displaySubmissions(submissionObjs)
    return displayMatches(submissionObjs)
    # return "<p>got data ok</p>"

# helper methods
# this method is for getting the submission responses from jotform via a form ID
def gatherSubmissionsFromForm(key, formId):
    jotform = JotformAPIClient(key)

    try:
        submissions = jotform.get_form_submissions(formId)
    except:
        return False

    return parseDataFromSubmissions(submissions)

# this method is for getting the submission responses from jotform via a comma separated list of submission IDs
def gatherSubmissionsFromList(key, idList):
    jotform = JotformAPIClient(key)
    submissionIds = idList.split(",")
    submissions = []


    for id in submissionIds:
        try:
            sub = jotform.get_submission(id)
        except:
            return False
        submissions.append(sub)

    return parseDataFromSubmissions(submissions)

# this method takes a list of submission responses (list of dictionaries) and parses the pertinent data out of them
# then creates usable submission objects and returns a list of those
def parseDataFromSubmissions(listOfSubmissions):
    parsedSubmissions = []

    for sub in listOfSubmissions:
        json_object = json.dumps(sub, indent=2)
        sub_json = json.loads(json_object)

        # empty vars to store submission info
        subId = sub_json["id"]
        creationDate = sub_json["created_at"]

        firstName = ""
        lastName = ""
        email = ""
        age = ""
        gender = ""
        eventDate = ""
        formAnswers = []
        formAnswersDict = {}

        if sub_json["status"] == "ACTIVE":
            for answer in sub_json["answers"]:
                # checks if answer is of type "control_matrix" (table that contains answers)
                if sub_json["answers"][answer]["type"] == "control_matrix":
                    for key in sub_json["answers"][answer]["answer"]:
                        resp = sub_json["answers"][answer]["answer"][key]
                        if resp == "Strongly Disagree":
                            formAnswers.append(0)
                            formAnswersDict[key] =  0
                        elif resp == "Disagree":
                            formAnswers.append(1)
                            formAnswersDict[key] =  1
                        elif resp == "Neither":
                            formAnswers.append(2)
                            formAnswersDict[key] =  2
                        elif resp == "Agree":
                            formAnswers.append(3)
                            formAnswersDict[key] =  3
                        elif resp == "Strongly Agree":
                            formAnswers.append(4)
                            formAnswersDict[key] =  4
                # check if answer is personal info
                elif sub_json["answers"][answer]["name"] == "firstName":
                    firstName = sub_json["answers"][answer]["answer"]
                elif sub_json["answers"][answer]["name"] == "lastName":
                    lastName = sub_json["answers"][answer]["answer"]
                elif sub_json["answers"][answer]["name"] == "email":
                    email = sub_json["answers"][answer]["answer"]
                elif sub_json["answers"][answer]["name"] == "age":
                    age = sub_json["answers"][answer]["answer"]
                elif sub_json["answers"][answer]["name"] == "eventDate":
                    eventDate = sub_json["answers"][answer]["answer"]
                elif sub_json["answers"][answer]["name"] == "gender":
                    try:
                        gender = sub_json["answers"][answer]["answer"]
                    except:
                        gender = "NULL"

            # create a submission object with all the gathered data connected to it
            parsedSubmissions.append(submission.Submission(subId, firstName, lastName, email, age, gender, formAnswersDict, creationDate, eventDate))

    return parsedSubmissions

# this method takes a list of submission objects and lists them by gender
def displaySubmissions(formattedSubmissions):
    lines = ["<!doctype html><html><head><title>Submissions</title></head><body>"]
    returnStr = ""

    lines.append("<h3>Males</h3>\n<ol>")
    for sub in formattedSubmissions:
        if sub.getGender() == "Male":
            #https://www.jotform.com/submission/235194815571509962
            lines.append("<li><a href='https://www.jotform.com/submission/" + sub.getId() + "'>" + sub.getFullName() + "</a></li>")

    lines.append("</ol><br><h3>Females</h3>\n<ol>")
    for sub in formattedSubmissions:
        if sub.getGender() == "Female":
            #https://www.jotform.com/submission/235194815571509962
            lines.append("<li><a href='https://www.jotform.com/submission/" + sub.getId() + "'>" + sub.getFullName() + "</a></li>")

    for line in lines:
        returnStr += line

    return returnStr

def displayMatchesWithPreferences(formattedSubmissions):
    matches = stablemarriages.getStableMarriages(formattedSubmissions)
    returnStr = "<!doctype html><html><head><title>Matches</title></head><body>"

    returnStr += "<h3>Matches</h3>"
    
    iterator = 1
    for male in matches.keys():
        maleSubmissionLink = "https://www.jotform.com/submission/" + male.getId()
        femaleSubmissionLink = "https://www.jotform.com/submission/" + matches[male].getId()
        returnStr += "<h4>Match " + str(iterator) + "</h3>"
        # returnStr += "<a href='https://www.jotform.com/submission/" + male.getId() + "'>" + male.getFullName() + "</a> + " + "<a href='https://www.jotform.com/submission/" + matches[male].getId() + "'>" + matches[male].getFullName() + "</a><br>"
        returnStr += "{} ({}) (<a href='{}'>View Submission</a>) + {} ({}) (<a href=''>View Submission</a>)<br>".format(male.getFullName(), male.getEmail(), maleSubmissionLink, matches[male].getFullName(), matches[male].getEmail(), femaleSubmissionLink)
        
        returnStr += "<strong>" + male.getFullName() + " Preferences: </strong><br>["
        for preference in male.getPreferenceList():
            returnStr += "{} ({}%), ".format(preference.getFullName(), str(stablemarriages.getPercentageOfSimilarAnswers(male, preference)))
        returnStr = returnStr[:-2]
        returnStr += "]<br>"

        returnStr += "<strong>" + matches[male].getFullName() + " Preferences: </strong><br>["
        for preference in matches[male].getPreferenceList():
            returnStr += "{} ({}%), ".format(preference.getFullName(), str(stablemarriages.getPercentageOfSimilarAnswers(matches[male], preference)))
        returnStr = returnStr[:-2]
        returnStr += "]<br>"

        returnStr += "-----------------------"
        iterator += 1

    returnStr += "</body></html>"
    return returnStr

def displayMatches(formattedSubmissions):
    matches = stablemarriages.getStableMarriages(formattedSubmissions)
    returnStr = "<!doctype html><html><head><title>Matches</title></head><body>"

    returnStr += "<h3>Matches</h3>\n<ol>"

    iterator = 1
    for male in matches.keys():
        maleSubmissionLink = "https://www.jotform.com/submission/" + male.getId()
        femaleSubmissionLink = "https://www.jotform.com/submission/" + matches[male].getId()
        returnStr += "<li>{} ({}) + {} ({})</li>".format(male.getFullName(), male.getEmail(), matches[male].getFullName(), matches[male].getEmail())

        iterator += 1

    returnStr += "</ol>"
    returnStr += "</body></html>"

    return returnStr