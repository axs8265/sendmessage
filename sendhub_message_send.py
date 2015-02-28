from flask import Flask, jsonify
from flask import request
from flask import abort
import operator

app = Flask(__name__)

output = {}

@app.route('/sendhub/sendmessage', methods=['POST'])
def send_message():
    
	#if the message does not contain required fields, then abort with bad request message
    if not request.json or not 'recipients' in request.json or not 'message' in request.json:
        abort(400)

    output['message'] = request.json['message']
    output['routes'] = assign_subnets(request.json['recipients'])
    return jsonify(output), 201

def assign_subnets(json_recipients):
    '''This method accepts recipients list and assigns 
    optimal number of recipients for each subnet avaliable. The subnets details are hardcoded inside this  function'''
    
    #Sanitize data first so that we can committ to the subnet allocation later
    json_recipients, errorneous_recipients = sanitize_mobile_numbers(json_recipients)

    if len(errorneous_recipients) > 0:        
        output['invalids'] = errorneous_recipients

    #Get the number of recipients
    no_of_recipients = len(json_recipients)    
    
    #Declare a dictionary containing the key as category and value as a list of a)IP b)throughput and c)allocatted subnet (which initially is 0)
    #this makes the code look a bit complex in the decendant functions but decreases the point of change in case more subnets are included
	#Note: this can even be converted out as a class object and used more fluently in a more complex scenario
    subnet_metadata = {'small': ['10.0.1.0',1,0], 'medium': ['10.0.2.0',5,0], 'large': ['10.0.3.0',10,0], 'super': ['10.0.4.0',25,0]}

    #Start with highest throughput to achive optimal distribution
    if no_of_recipients >= int(subnet_metadata['super'][1]):
        no_of_recipients, subnet_metadata['super'][2] = subnet_allocation(no_of_recipients, int(subnet_metadata['super'][1]))

    if no_of_recipients >= int(subnet_metadata['large'][1]):
        no_of_recipients, subnet_metadata['large'][2] = subnet_allocation(no_of_recipients, int(subnet_metadata['large'][1]))

    if no_of_recipients >= int(subnet_metadata['medium'][1]):
        no_of_recipients, subnet_metadata['medium'][2] = subnet_allocation(no_of_recipients, int(subnet_metadata['medium'][1]))

    if no_of_recipients >= int(subnet_metadata['small'][1]):
        no_of_recipients, subnet_metadata['small'][2] = subnet_allocation(no_of_recipients, int(subnet_metadata['small'][1]))
        
    return creat_output(subnet_metadata, json_recipients)


def subnet_allocation(no_of_recipients, subnet_throughput):
    '''This funciton returns the number of recipients for a given subnet throughput and adjusts remaining recipients accordingly'''
    recipient_per_subnet = 0
    if no_of_recipients%subnet_throughput == 0:
            recipient_per_subnet = no_of_recipients/subnet_throughput
            return 0, recipient_per_subnet
    else:
        #perform a floor division since we are intrested only the integer result
        recipient_per_subnet = no_of_recipients//subnet_throughput 
        #adjust the remaining number of recipients
        no_of_recipients = no_of_recipients - recipient_per_subnet*subnet_throughput       
        return no_of_recipients, recipient_per_subnet

def create_output(subnet_meta, json_recipients):
    '''This function creates the output list based on the recipient distrubution per subnet category'''
    result_list = []

    for key in subnet_meta:
         #Check recipient count for each subnet and remove the allocated number of recipients from the input list
        if subnet_meta[key][2] > 0:
            route = {'ip': subnet_meta[key][0] }
            #get the allocated recipients fromt he top of the list
            route['recipients'] = json_recipients[:int(subnet_meta[key][1])*int(subnet_meta[key][2])]
            #Add them to the result list
            result_list.append(route)
            #delete the assigned recipients from the main input list
            del json_recipients[:int(subnet_meta['super'][1])*int(subnet_meta['super'][2])]

    return result_list

def sanitize_mobile_numbers(json_recipients):
    '''This funciton check validity of every phone number in the recipient list'''
    valid_recipients = []
    errorneous_recipients = []

    for ph_number in json_recipients:
        #check if this a 10 digit number
        if len(ph_number) == 10:
            #Length is fine, but is it a valid number
            try:
                temp = int(ph_number)
                valid_recipients.append(ph_number)
            except ValueError:
                #Unable to parse it as int. Can't be a valid number
                errorneous_recipients.append(ph_number)                
        else:
            errorneous_recipients.append(ph_number)

    return valid_recipients, errorneous_recipients



if __name__ == '__main__':
    app.run(debug=True)
