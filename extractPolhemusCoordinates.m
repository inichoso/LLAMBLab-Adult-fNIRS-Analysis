%% ============================================================
% EXTRACT POLHEMUS OPTODE AND NIRS CHANNEL COORDINATES
%
% This script:
%
% 1. Loads a processed Polhemus .mat file
% 2. Extracts all optode/landmark coordinates
% 3. Saves the optode coordinates
% 4. Recreates the 108 NIRS channel coordinates using the
%    transmitter/receiver midpoint exactly as in the original
%    NIRS processing script
% 5. Compares those coordinates with channelsOptodes.xlsx
%
% ============================================================

%% ============================================================
% 1. FILE PATHS
% ============================================================

% -------------------------------------------------------------
% Processed Polhemus file
% -------------------------------------------------------------

polhemusFile = ...
    '/Users/in65/Desktop/3DScans/0CD703D8MOV_2021-07-26_Full_Head_NIRx09-20-15-30.mat';


% -------------------------------------------------------------
% Optode labels
% -------------------------------------------------------------

optodeLabelFile = ...
    '/Users/in65/Desktop/nirsNiiFiles/optodeLabels.xlsx';


% -------------------------------------------------------------
% Channel mapping
% -------------------------------------------------------------

channelFile = ...
    '/Users/in65/Desktop/nirsNiiFiles/channels.xlsx';


% -------------------------------------------------------------
% Existing channel-coordinate spreadsheet
% -------------------------------------------------------------

channelCoordinateFile = ...
    '/Users/in65/Desktop/nirsNiiFiles/channelsOptodes.xlsx';


% -------------------------------------------------------------
% Output directory
% -------------------------------------------------------------

outputDir = ...
    '/Users/in65/Desktop/nirsNiiFiles/PolhemusCoordinates';

if ~exist(outputDir,'dir')
    mkdir(outputDir);
end


%% ============================================================
% 2. LOAD POLHEMUS FILE
% ============================================================

fprintf('\n============================================\n');
fprintf('LOADING POLHEMUS FILE\n');
fprintf('============================================\n');

fprintf('\nFile:\n%s\n\n',polhemusFile);

P = load(polhemusFile);

fprintf('Variables contained in file:\n');
disp(fieldnames(P));


%% ============================================================
% 3. CHECK FOR POLHEMUS OBJECT
% ============================================================

if ~isfield(P,'polhemus')

    error(['The loaded file does not contain a variable ', ...
        'named "polhemus".']);

end


polhemus = P.polhemus;

fprintf('\nPolhemus object found.\n');

fprintf('Class:\n');
disp(class(polhemus));


%% ============================================================
% 4. CHECK POLHEMUS DATA
% ============================================================

if ~isprop(polhemus,'data') && ...
        ~isfield(polhemus,'data')

    error(['The Polhemus object does not appear to contain ', ...
        'a "data" property.']);

end


data = polhemus.data;

fprintf('\nPolhemus data class:\n');
disp(class(data));


%% ============================================================
% 5. GET ALL OPTODE/LANDMARK NAMES
% ============================================================

% Your original script accesses the coordinates with:
%
% xyzParticipant.polhemus.data(opt)
%
% which indicates that "data" is a containers.Map.

if isa(data,'containers.Map')

    optNames = data.keys;

else

    error(['polhemus.data is not a containers.Map. ', ...
        'Class found: ',class(data)]);

end


fprintf('\nNumber of entries in Polhemus data: %d\n', ...
    length(optNames));


%% ============================================================
% 6. EXTRACT ALL POLHEMUS COORDINATES
% ============================================================

nOptodes = length(optNames);

optodeNames = strings(nOptodes,1);

optodeX = NaN(nOptodes,1);
optodeY = NaN(nOptodes,1);
optodeZ = NaN(nOptodes,1);


for i = 1:nOptodes

    name = optNames{i};

    coord = data(name);

    % Make sure coordinate is a vector
    coord = coord(:);

    if length(coord) < 3

        warning( ...
            'Skipping %s: coordinate has fewer than 3 values.', ...
            name);

        continue;

    end

    optodeNames(i) = string(name);

    optodeX(i) = coord(1);
    optodeY(i) = coord(2);
    optodeZ(i) = coord(3);

end


%% ============================================================
% 7. CREATE OPTODE TABLE
% ============================================================

optodeTable = table( ...
    optodeNames, ...
    optodeX, ...
    optodeY, ...
    optodeZ, ...
    'VariableNames', ...
    {'Optode','X','Y','Z'});


%% ============================================================
% 8. DISPLAY ALL OPTODE COORDINATES
% ============================================================

fprintf('\n============================================\n');
fprintf('POLHEMUS OPTODE COORDINATES\n');
fprintf('============================================\n');

disp(optodeTable);


%% ============================================================
% 9. DISPLAY COORDINATE RANGES
% ============================================================

fprintf('\nCoordinate ranges:\n');

fprintf('X: %.3f to %.3f\n', ...
    min(optodeX,[],'omitnan'), ...
    max(optodeX,[],'omitnan'));

fprintf('Y: %.3f to %.3f\n', ...
    min(optodeY,[],'omitnan'), ...
    max(optodeY,[],'omitnan'));

fprintf('Z: %.3f to %.3f\n', ...
    min(optodeZ,[],'omitnan'), ...
    max(optodeZ,[],'omitnan'));


%% ============================================================
% 10. SAVE OPTODE COORDINATES
% ============================================================

optodeExcel = fullfile( ...
    outputDir, ...
    'Polhemus_optode_coordinates.xlsx');

writetable(optodeTable,optodeExcel);


optodeMat = fullfile( ...
    outputDir, ...
    'Polhemus_optode_coordinates.mat');

save(optodeMat,'optodeTable');


fprintf('\nSaved optode coordinates:\n%s\n', ...
    optodeExcel);

fprintf('%s\n',optodeMat);


%% ============================================================
% 11. LOAD ORIGINAL OPTODE LABEL LIST
% ============================================================

fprintf('\n============================================\n');
fprintf('LOADING OPTODE LABEL LIST\n');
fprintf('============================================\n');

optLabels = readtable(optodeLabelFile);

optNum = string(optLabels{:,'Optodes'});

fprintf('Number of optodes in label spreadsheet: %d\n', ...
    length(optNum));


%% ============================================================
% 12. CREATE "KEYS" EXACTLY AS ORIGINAL SCRIPT
% ============================================================

keys = [];

validOptodes = strings(0,1);

for s = 1:length(optNum)

    opt = optNum(s);

    % Convert string to character if needed
    optChar = char(opt);

    if isKey(data,optChar)

        newOpt = data(optChar);

        newOpt = newOpt(:);

        if length(newOpt) >= 3

            keys = [keys; newOpt(1:3)'];

            validOptodes(end+1,1) = opt;

        end

    else

        warning( ...
            'Optode %s not found in Polhemus file.', ...
            opt);

    end

end


fprintf('\nNumber of optodes successfully loaded: %d\n', ...
    size(keys,1));


%% ============================================================
% 13. LOAD CHANNEL MAPPING
% ============================================================

fprintf('\n============================================\n');
fprintf('LOADING CHANNEL MAPPING\n');
fprintf('============================================\n');

allChannels = readtable(channelFile);

fprintf('Rows in channels.xlsx: %d\n', ...
    height(allChannels));


%% ============================================================
% 14. RECREATE THE SAME CHANNEL SELECTION
%     USED IN YOUR ORIGINAL SCRIPT
% ============================================================

channelRows = [ ...
    1:8, ...
    10:21, ...
    23:28, ...
    30:43, ...
    45:48, ...
    50:66, ...
    68:86, ...
    88:97, ...
    99:height(allChannels) ...
    ];


channelNum = table2array( ...
    allChannels(channelRows,[1 3 4]));


fprintf('Channels retained: %d\n', ...
    height(channelNum));


%% ============================================================
% 15. RECREATE CHANNEL COORDINATES
%     EXACTLY AS ORIGINAL SCRIPT
% ============================================================

nChannels = height(channelNum);

xyzPolhemus = NaN(nChannels,3);


for l = 1:nChannels

    chanT = channelNum(l,2);

    chanR = channelNum(l,3);


    % These channel numbers refer to the rows in "keys"
    % in the same way as your original script.

    if chanT > size(keys,1) || ...
            chanR > size(keys,1)

        warning( ...
            'Channel %d references an unavailable optode.', ...
            l);

        continue;

    end


    xyzPolhemus(l,:) = ...
        mean(keys([chanR chanT],:),1);

end


%% ============================================================
% 16. CREATE CHANNEL TABLE
% ============================================================

channelCoordinatesPolhemus = table( ...
    channelNum(:,1), ...
    channelNum(:,2), ...
    channelNum(:,3), ...
    xyzPolhemus(:,1), ...
    xyzPolhemus(:,2), ...
    xyzPolhemus(:,3), ...
    'VariableNames', ...
    {'Channel','Transmitter','Receiver', ...
     'X','Y','Z'});


%% ============================================================
% 17. DISPLAY CHANNEL COORDINATES
% ============================================================

fprintf('\n============================================\n');
fprintf('CHANNEL COORDINATES FROM POLHEMUS\n');
fprintf('============================================\n');

disp(channelCoordinatesPolhemus);


%% ============================================================
% 18. SAVE CHANNEL COORDINATES
% ============================================================

channelPolhemusExcel = fullfile( ...
    outputDir, ...
    'Polhemus_channel_coordinates.xlsx');

writetable( ...
    channelCoordinatesPolhemus, ...
    channelPolhemusExcel);


channelPolhemusMat = fullfile( ...
    outputDir, ...
    'Polhemus_channel_coordinates.mat');

save( ...
    channelPolhemusMat, ...
    'xyzPolhemus', ...
    'channelCoordinatesPolhemus');


fprintf('\nSaved Polhemus channel coordinates:\n%s\n', ...
    channelPolhemusExcel);


%% ============================================================
% 19. LOAD EXISTING CHANNEL COORDINATES FROM EXCEL
% ============================================================

fprintf('\n============================================\n');
fprintf('COMPARING WITH channelsOptodes.xlsx\n');
fprintf('============================================\n');

T = readtable(channelCoordinateFile);

fprintf('Rows in channelsOptodes.xlsx: %d\n', ...
    height(T));


%% ============================================================
% 20. RECREATE CHANNEL COORDINATES FROM EXCEL
% ============================================================

xyzExcel = [ ...
    (T.TX + T.RX)/2, ...
    (T.TY + T.RY)/2, ...
    (T.TZ + T.RZ)/2 ...
    ];


%% ============================================================
% 21. CHECK NUMBER OF CHANNELS
% ============================================================

if size(xyzExcel,1) ~= nChannels

    error(['The number of channels in channelsOptodes.xlsx ', ...
        'does not match the Polhemus channel count.']);

end


%% ============================================================
% 22. CALCULATE DIFFERENCE BETWEEN COORDINATE SETS
% ============================================================

coordinateDifference = ...
    xyzExcel - xyzPolhemus;


coordinateDistance = sqrt( ...
    sum(coordinateDifference.^2,2));


%% ============================================================
% 23. PRINT COMPARISON STATISTICS
% ============================================================

fprintf('\n============================================\n');
fprintf('COORDINATE COMPARISON\n');
fprintf('============================================\n');

fprintf('\nMean difference:   %.4f\n', ...
    mean(coordinateDistance,'omitnan'));

fprintf('Median difference: %.4f\n', ...
    median(coordinateDistance,'omitnan'));

fprintf('Maximum difference: %.4f\n', ...
    max(coordinateDistance,[],'omitnan'));

fprintf('Minimum difference: %.4f\n', ...
    min(coordinateDistance,[],'omitnan'));


%% ============================================================
% 24. DISPLAY FIRST 20 CHANNELS SIDE-BY-SIDE
% ============================================================

comparisonTable = table( ...
    T.Channel, ...
    xyzExcel(:,1), ...
    xyzExcel(:,2), ...
    xyzExcel(:,3), ...
    xyzPolhemus(:,1), ...
    xyzPolhemus(:,2), ...
    xyzPolhemus(:,3), ...
    coordinateDistance, ...
    'VariableNames', ...
    {'Channel', ...
     'ExcelX','ExcelY','ExcelZ', ...
     'PolhemusX','PolhemusY','PolhemusZ', ...
     'Distance'});


fprintf('\nFirst 20 channels:\n');

disp(comparisonTable(1:min(20,height(comparisonTable)),:));


%% ============================================================
% 25. IDENTIFY LARGE DIFFERENCES
% ============================================================

% A difference greater than 5 mm is flagged.

largeDifference = coordinateDistance > 5;


fprintf('\n============================================\n');
fprintf('LARGE COORDINATE DIFFERENCES (>5 mm)\n');
fprintf('============================================\n');

fprintf('Number of channels >5 mm different: %d\n', ...
    sum(largeDifference));


if any(largeDifference)

    disp(comparisonTable(largeDifference,:));

else

    fprintf('No channels differ by more than 5 mm.\n');

end


%% ============================================================
% 26. SAVE COMPARISON TABLE
% ============================================================

comparisonFile = fullfile( ...
    outputDir, ...
    'Polhemus_vs_Excel_channel_coordinates.xlsx');

writetable( ...
    comparisonTable, ...
    comparisonFile);


%% ============================================================
% 27. SAVE EVERYTHING AS MATLAB FILE
% ============================================================

save( ...
    fullfile(outputDir, ...
    'Coordinate_comparison.mat'), ...
    'optodeTable', ...
    'channelCoordinatesPolhemus', ...
    'xyzPolhemus', ...
    'xyzExcel', ...
    'comparisonTable', ...
    'coordinateDistance');


%% ============================================================
% 28. FINAL SUMMARY
% ============================================================

fprintf('\n\n============================================\n');
fprintf('COMPLETE\n');
fprintf('============================================\n');

fprintf('\nOptodes extracted: %d\n', ...
    nOptodes);

fprintf('NIRS channels reconstructed: %d\n', ...
    nChannels);

fprintf('\nPolhemus coordinate file:\n%s\n', ...
    channelPolhemusExcel);

fprintf('\nExcel comparison file:\n%s\n', ...
    comparisonFile);

fprintf('\nMean coordinate difference: %.4f mm\n', ...
    mean(coordinateDistance,'omitnan'));

fprintf('Median coordinate difference: %.4f mm\n', ...
    median(coordinateDistance,'omitnan'));

fprintf('\nIf the coordinate differences are near zero,\n');
fprintf('the channelsOptodes.xlsx coordinates reproduce\n');
fprintf('the coordinates from the Polhemus processing.\n');