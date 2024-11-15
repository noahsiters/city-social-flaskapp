from flask import Flask
from flask import render_template
from flask import request
from flask import redirect

from io import StringIO
from jotform import JotformAPIClient

import pandas as pd
import json
import submission
import stablemarriages

app = Flask(__name__)

# index page route
@app.route("/")
@app.route("/<key>")
def index(key=None):
    # when going to index page, render the index.html template
    return render_template("index.html", key=key)

# form action - this method is called when the form is submitted
@app.route("/f_dataInput", methods=["POST"])
def dataInput():
    # check if api key is valid
    try:
        jotform = JotformAPIClient(request.form["apikey"])
        user = jotform.get_user()
        key  = request.form["apikey"]
    except:
        return redirect("/BadKey")
        
    # get form data
    requestedDate = request.form['eventDate']
    includePrefList = request.form.get("preferenceListCheckbox")

    # get input type
    try:
        inputType = request.form['inputType']
    except:
        return redirect("/NoInputType")
    
    # check if we are filtering by event date
    if requestedDate != '':
        requestedDate = reformatDate(requestedDate) # reformats date to MM/DD/YY
    else:
        requestedDate = False
    
    # check if we are processing via file or form id/submission ids and get data accordingly
    data = ''
    if inputType == 'file_upload':
        try:
            rawFile = request.files['file']
            df = pd.read_csv(StringIO(rawFile.read().decode('utf-8')))
        except:
            return redirect("/NoFile")
        
        data = df
    elif inputType == 'id_input':
        try:
            id = request.form['submissionId']
        except:
            return redirect("/BadForm")
        
        data = id

        if id == '':
            return redirect("/BadForm")
        
        if ',' in id:
            inputType += '_submissions'
        else:
            inputType += '_form'

    submissionObjs = gatherSubmissionsFromJotform(key, inputType, data, requestedDate)

    # output
    if submissionObjs == False:
        return redirect("/BadForm")
    
    if includePrefList == "Yes":
        return displayMatchesWithPreferences(submissionObjs)
    else:
        return displayMatches(submissionObjs)

# helper methods
def gatherSubmissionsFromJotform(key, inputType, data, requestedDate):
    jotform = JotformAPIClient(key)
    submission_id_list = []
    submissions = []

    if inputType == 'file_upload' or inputType == 'id_input_submissions':
        if inputType == 'file_upload':
            submission_id_list = data['Submission ID'].tolist()
        elif inputType == 'id_input_submissions':
            submission_id_list = data.split(',')

        for id in submission_id_list:
            try:
                sub = jotform.get_submission(str(id))
            except:
                return False
            
            submissions.append(sub)

    elif inputType == 'id_input_form':
        submissions = jotform.get_form_submissions(data)

    return parseDataFromSubmissions(submissions, requestedDate)

# this method takes a list of submission responses (list of dictionaries) and parses the pertinent data out of them
# then creates usable submission objects and returns a list of those
def parseDataFromSubmissions(submissions, requestedDate):
    submissionObjs = []

    for sub in submissions:
        json_object = json.dumps(sub, indent=2)
        sub_json = json.loads(json_object)

        subId = sub_json['id']
        creationDate = sub_json['created_at']
        eventDate = ''

        # confirm that the submission is ACTIVE and not DELETED
        if sub_json['status'] == 'ACTIVE':
            # get the event date of the submission
            for answer in sub_json['answers']:
                if sub_json['answers'][answer]['name'] == 'eventDate':
                    eventDate = sub_json['answers'][answer]['answer']
            
            # check if we are filtering for event date
            if requestedDate != False:
                # only get submissions with matching event date
                if eventDate == requestedDate:
                    submissionData = parseSubmissionAnswers(sub_json['answers'])
                    submissionObjs.append(submission.Submission(subId, submissionData['firstName'], submissionData['lastName'], submissionData['email'], submissionData['age'], submissionData['gender'], submissionData['formAnswersDict'], creationDate, eventDate))

            else:
                # get all submissions
                submissionData = parseSubmissionAnswers(sub_json['answers'])    
                submissionObjs.append(submission.Submission(subId, submissionData['firstName'], submissionData['lastName'], submissionData['email'], submissionData['age'], submissionData['gender'], submissionData['formAnswersDict'], creationDate, eventDate))

    return submissionObjs

# uses switch case to go through each answer in json and store it in a dictionary
def parseSubmissionAnswers(subAnswers):
    submissionData = {
        'firstName': '',
        'lastName': '',
        'email': '',
        'age': '',
        'gender': '',
        'formAnswers': '',
        'formAnswersDict': ''
    }

    formAnswers = []
    formAnswersDict = {}

    for answer in subAnswers:
        # checks if answer is of type "control_matrix" (table that contains answers)
        if subAnswers[answer]['type'] == 'control_matrix':
            for key in subAnswers[answer]['answer']:
                resp = subAnswers[answer]['answer'][key]
                match resp:
                    case 'Strongly Disagree':
                        formAnswers.append(0)
                        formAnswersDict[key] = 0
                    case 'Disagree':
                        formAnswers.append(1)
                        formAnswersDict[key] = 1
                    case 'Neither':
                        formAnswers.append(2)
                        formAnswersDict[key] = 2
                    case 'Agree':
                        formAnswers.append(3)
                        formAnswersDict[key] = 3
                    case 'Strongly Agree':
                        formAnswers.append(4)
                        formAnswersDict[key] = 4
        # check if answer is personal info
        match subAnswers[answer]['name']:
            case 'firstName':
                submissionData['firstName'] = subAnswers[answer]['answer']
            case 'lastName':
                submissionData['lastName'] = subAnswers[answer]['answer']
            case 'email':
                submissionData['email'] = subAnswers[answer]['answer']
            case 'age':
                submissionData['age'] = subAnswers[answer]['answer']
            case 'gender':
                try:
                    submissionData['gender'] = subAnswers[answer]['answer']
                except:
                    submissionData['gender'] = False
    
    submissionData['formAnswers'] = formAnswers
    submissionData['formAnswersDict'] = formAnswersDict
    return submissionData

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
    print(str(matches))
    for male in matches.keys():
        maleSubmissionLink = "https://www.jotform.com/submission/" + male.getId()
        femaleSubmissionLink = "https://www.jotform.com/submission/" + matches[male].getId()
        returnStr += "<li>{} ({}) + {} ({})</li>".format(male.getFullName(), male.getEmail(), matches[male].getFullName(), matches[male].getEmail())

        iterator += 1

    returnStr += "</ol>"
    returnStr += "</body></html>"

    return returnStr

# reformat date from YYYY-MM-DD to MM/DD/YY
def reformatDate(date):
    dateArr = date.split('-')

    # shorten year to two digits
    if len(dateArr[0]) == 4:
        dateArr[0] = dateArr[0][-2:]

    newDateStr = dateArr[1] + "/" + dateArr[2] + "/" + dateArr[0]
    return newDateStr