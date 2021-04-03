
# Create an env.list file containing the temporary AWS credentials
# This syntax allows to call a function (get_session_creds) declared in another shell file
. ./get_session_creds.sh
# echo "Reading iamroles.txt"
creds=$(get_session_creds)
