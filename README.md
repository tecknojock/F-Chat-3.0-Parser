# F-Chat-3.0-Parser
Parser for F-Chat 3.0 database style logs


                                                                                                
                                     F-Chat 3.0 Log Parser                                      
                                       Author: GyroTech                                         
                                                                                                
                                        1.1.1-11/30/2022                                            
                                                                                                
  This script parses out the database logs that fchat spits out, and then turns them into       
  plain text. The script automatically remembers when you last ran it, and will append to       
  existing logs. Note, this only works for the desktop version of f-chat.                       
                                                                                                
  Usage: Update the variables below and then run it. If you want to rerun the full export,      
  delete the lastrun.txt file in your plain text log folder. Note, this script appends to the   
  logs, so it will duplicate unless you delete the folders you intend to rerun.                  
                                                                                                
                                                                                                
Changelog: 

1.0.0 : Release

1.0.1: Improved the last run time so that it took the latest line logged, rather than the current time.

1.1.0: Added support for multiple characters.

1.1.1: Added a handler for a logging error F-chat occasionally inserts into the database.

1.1.2: Ignores console due to weird output.

1.1.3: Made it so that start time is always the latest run-time if run-time exceeds. This will result in a few duplicate logs if run while f-chat is live, but better than dropping logs that come in while the application is running. Also makes the parser more robust to handle weird errors that occasionally crop up. It looks for names instead of trusting the file structure to be correct.
