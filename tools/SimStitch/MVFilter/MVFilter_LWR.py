import shutil
import tempfile
import os
import optparse
import traceback
import sys

from galaxy.jobs.runners.lwr_client import Client, url_to_destination_params, FileStager
from galaxy.jobs import JobDestination

class MockTool(object):

    def __init__(self, tool_dir):
        self.id = "client_test"
        self.version = "1.0"
        self.tool_dir = tool_dir



def main():
    """ Exercises a running lwr server application with the lwr client. """
    parser = optparse.OptionParser()
    parser.add_option('--url', dest='url', default='localhost')
    parser.add_option('--key', dest = 'private_token', default=None)
    parser.add_option('--port',dest = 'port',default='8913')
    parser.add_option('--outfile',dest='outfile',default='results.txt')

    parser.add_option('--infile', dest='infile',default=None)
    parser.add_option('--numscans', dest='numscans',default=0 )
    parser.add_option( '--mintic', dest='mintic',default=0)
    parser.add_option( '--ignorecal', dest='ignorecal',default=False)
    parser.add_option( '--maxmz', dest='maxmz',default=0)	
    (options, args) = parser.parse_args()


    if options.private_token == 'None':
	options.private_token = None


    options.url = 'http://'+str(options.url)+':'+str(options.port)+'/'



    try:
	

        temp_directory = tempfile.mkdtemp()
        temp_work_dir = os.path.join(temp_directory, "w")
        #temp_tool_dir = os.path.join(temp_directory, "t")

        #for dir in [ temp_work_dir,temp_tool_dir]:
	for dir in [ temp_work_dir]:
            os.makedirs(dir)

        temp_input_path = os.path.join(temp_directory, "input.txt")
        temp_config_path = os.path.join(temp_work_dir, "config.txt")
        #temp_tool_path = os.path.join(temp_tool_dir, "basicMatlab_LWR.m")
	#temp_tool_command = "basicMatlab_LWR"

	################################################################Couldn't get this to find a matlab script
	perm_tool_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"basicMatlab_LWR")
	perm_tool_file = "basicMatlab_LWR.m"
	perm_tool_command = "basicMatlab_LWR"
	perm_tool_path = os.path.join(perm_tool_dir, perm_tool_file)
	#################################################################Had to create manually in this script- see below

        temp_output_path = os.path.join(temp_directory, options.outfile)

        temp_input_file = open(temp_input_path, "w")
        temp_config_file = open(temp_config_path, "w")
        #temp_tool_file = open(temp_tool_path, "w")


    except:
	error_file = open(options.outfile, 'w')
	error_file.write("Problem with creating temp files!")
	error_file.close()
	return




    try:
    	temp_input_file.write("There are no frigging inputs")
    	temp_config_file.write("And no muppet frigging configs")
    	


    except:
	error_file = open(options.outfile, 'w')
	error_file.write("Problem with writing to temp files!")
	error_file.close()
	return

    finally:
    	temp_input_file.close()
        temp_config_file.close()

    try:	

	# instantiate a client and stager with the location of the matlab script to be called
	command_line1 = '%s' %(perm_tool_path)
    	config_files = [temp_config_path]
    	input_files = [temp_input_path]
    	output_files = [temp_output_path]
	client1 = Client(url_to_destination_params( options.url ),'123456')
	stager1 = FileStager(client1, MockTool(perm_tool_dir), command_line1, config_files, input_files, output_files, temp_work_dir)

	#poll the LWR server for its local version of the matlab tool
	new_command1 = stager1.get_rewritten_command_line()

	# extract the tool directory only (we know what the file name is)	
	temp_tool_dir_trans, separator, file_name = new_command1.rpartition('\\') 	#WINDOWS

	if temp_tool_dir_trans:
		LWR_OS = 'win'
	else:
		LWR_OS = 'nix'
		temp_tool_dir_trans, separator, file_name = new_command1.rpartition('/')	#*NIX


	#kill the client and remove all directories on the LWR server so they can be reused
	client1.clean()	

    	
	#REPEAT TO GET translated temp_output_path (for this example that's all we need)

	command_line1 = '%s' %(temp_output_path)
    	config_files = [temp_config_path]
    	input_files = [temp_input_path]
    	output_files = [temp_output_path]
	client1 = Client(url_to_destination_params( options.url ),'123456')
	stager1 = FileStager(client1, MockTool(perm_tool_dir), command_line1, config_files, input_files, output_files, temp_work_dir)
	new_command1 = stager1.get_rewritten_command_line()

    	#the LWR server local path for the output file will be used as an input for the Matlab script
	temp_output_path_trans = new_command1

	#kill the client and remove all directories on the LWR server so we can reuse them
	client1.clean()	


	#USE BOTH TRANSLATED PATHS TO MAKE A FINAL COMMAND LINE

	if LWR_OS=="win":
		com_line1 = "matlab -nosplash -nodesktop -minimize -wait -r " #for WINDOWS
	else:
		com_line1 = "matlab -nosplash -r " #for Mac, -nodesktop stops Matlab from exiting or something (testing on my laptop)


	com_line2 = '"cd '	
	com_line3 = "'%s';%s('%s');exit;" %(temp_tool_dir_trans,perm_tool_command, temp_output_path_trans)
	#com_line4 = '" -logfile lwr_job_log.txt' #for bug testing 
	com_line4 = '"'
	com_line_final = com_line1+com_line2+com_line3+com_line4


 
    	config_files = [temp_config_path]
    	input_files = [temp_input_path]
    	output_files = [temp_output_path]


	#CREATE A DUMMY COMMAND LINE THAT CONTAINS THE NECESSARY TOOLS AND FILES TO BE PASSED OVER ON FINAL RUN

	#command_line_dummy = '%s %s' %(temp_tool_path, temp_output_path)
	command_line_dummy = '%s %s' %(perm_tool_path, temp_output_path)	

	#recreate the client - WITH THE SAME JOB NUMBER - in the hopes of keeping same translation of directories
	client2 = Client(url_to_destination_params( options.url ),'123456')
	#stager2 = FileStager(client2, MockTool(temp_tool_dir), command_line_dummy, config_files, input_files, output_files, temp_work_dir)
	stager2 = FileStager(client2, MockTool(perm_tool_dir), command_line_dummy, config_files, input_files, output_files, temp_work_dir)

        #client = Client({"url": options.url, "private_token": options.private_token}, "123456")
    	#client = Client(url_to_destination_params( options.url ),'123456')
    	#stager = FileStager(client, MockTool(temp_tool_dir), command_line, config_files, input_files, output_files, temp_work_dir)

	



    	new_command = stager2.get_rewritten_command_line() #ignore this
	
	

	#finally send the pre-translated, final command line via the client
    	client2.launch(com_line_final)
    	client2.wait()
    	client2.download_output(temp_output_path, temp_directory)
    	output_file = open(temp_output_path, 'r')
    	output_file.close()


    finally:
        shutil.rmtree(temp_directory)
        client2.clean()

if __name__ == "__main__":
    main()

