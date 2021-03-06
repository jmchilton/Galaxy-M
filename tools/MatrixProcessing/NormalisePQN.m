function [dtst_out, coeffs,peaks_used]=Normalise_PQN_BB(dso_xml, outfile)
% -------------------------------------------------------------------
% Adaptation of standard PQN 
% uses only 'included' samples to create reference spectrum (e.g. QCs only)
% Then normalises each spectrum using the subset of peaks shared by that spectrum and the reference.
% This means that each spectrum is normalised using a slightly different subset of peaks.
% This is useful if there are many missing values (hence name of script).
% 
% NB: this algorithm uses the mean of all spectra (in the 100% filtered
% matrix) as the reference spectrum.
%
% Usage: 
% Normalise_PQN_Galaxy(SET,outfile)
%
%   inputs: 
%           SET: the number produced by FileListManagerGUI. The script will
%           use this to find the dataset object to be normalised
%
%           outfile: Galaxy will pass the name of an output file for the script will produce a status update file for
%           returning to Galaxy.
%
%   outputs:
%           
%           dtst_out: the normalised full matrix will be saved to the
%           project's DSO folder
%           coeff: the PQN coefficients for each sample may be returned to Galaxy in a future edition. 
% 
%   R L Davidson, 19th January 2012
% -------------------------------------------------------------------


%% CHECK FOR PLS TOOLBOX IN PATH

try
    dtst = dataset(rand(10,100));       %attempt to create a dataset object
    props = properties(dtst);           %request the properties of said object
catch err
    if strcmp(err.identifier,'MATLAB:UndefinedFunction') %if dataset function not available then neither PLS Toolbox or Stats Toolbox are installed.
        
        fid = fopen(outfile,'w');
        fprintf(fid,'Matlab does not recognise dataset function. Neither PLSToolbox or Stats toolbox installed. Please amend and try again.');
        fclose(fid);
        return

    end
end





if ~isempty(props) %PLS Toolbox datasets have no properties at initiation whereas Matlab datasets have 2.
    
    % if here, Statistics Toolbox version has been used. need to move stats toolbox below pls toolbox.
    clear dtst
    clear classes   %need to remove the statistics toolbox dataset class
    
    original_path = path; %save original path
    rem = original_path;
    pls_path = '';
    rem_path = '';
    while true
        [str,rem] = strtok(rem,pathsep);
        if isempty(str)
            break
        elseif strfind(str,'pls_toolbox') %covers all pls_toolbox entries
            pls_path = [pls_path,str,pathsep];
        else
            rem_path = [rem_path,str,pathsep];
        end
    end
    
    if ~isempty(pls_path) %check for no PLS toolbox installed
        path(pls_path,rem_path); %put PLS at the top!
        rehash pathreset;
        rehash toolboxreset;
        
        dtst = dataset(rand(10,100));
        props = properties(dtst);
        if ~isempty(props) % if rehash has not worked, quit.
            fid = fopen(outfile,'w');
            fprintf(fid,'Cannot appropriately rejig path. Please manually place PLSToolbox above Stats Toolbox in path.');
            fclose(fid);
            path(original_path);
            return
        end
        
    else    % If no stats toolbox entries have been found in path there is a more serious problem.
        fid = fopen(outfile,'w');
        fprintf(fid,'PLS Toolbox not on path. Please Install and try again.');
        fclose(fid);
        path(original_path);
        return
    end
    
else
    sprintf('PLS Toolbox dataset objects are available. Continuing.')
    original_path = path;
end



%% GET DATA FROM FILELIST OBJECT
%load data

[dtst, name, source] = autoimport(dso_xml, 'xml');


%% DATA EXTRACTION

x = dtst.data; %all data

inc = dtst.include{1};
y = x(inc,:); %qcs or subset of data to be used to create reference spectrum.

%% NORMALISE 
ref = mean(y);  %uses only 'included' samples to make the reference
peaks_used = zeros(1,size(x,1));    %for storing details
coeffs = zeros(size(x,1),1);        %for stoting details

% Loop for every sample, comparing each to the reference. 
% Use only the shared peaks between sample 'i' and reference
% This subset will be different for each sample so number of 'peaks_used' are
% retained in each case.
for i = 1:size(x,1)
    %step 1: find the sub-matrix that has no missing values
    tmp_mat = [ref;x(i,:)];
    ind = find(min(tmp_mat)>0);
    
    peaks_used(i) = length(ind);
    ref_temp = ref(ind);
    spec_temp = x(i,ind);
    coeffs(i) = median(spec_temp./ref_temp); %find the median coefficient
end

%step 3: apply normalisation to full matrix

%create coeff matrix
coeff_mat = repmat(coeffs,1,size(x,2));
%divide all by coeffs. 
x = x./coeff_mat;


% return output as dataset object or matrix.
dtst_out = dtst;
dtst_out.data = x;
dtst_out.name=[dtst.name,'_pqn'];

%export DSO to XML
autoexport(dtst_out, outfile, 'xml');


%% RETURN PATH TO NORMAL
path(original_path);
rehash pathreset;
rehash toolbox;

return
end
