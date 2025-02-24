###################################
# .sh file to build every container
###################################

# Define the list_of_directories containing dir_1 and dir_2
list_of_directories=("backend" "frontend")

# Loop through each directory
for dir in "${list_of_directories[@]}"; do
    # Change directory to the current directory in the loop
    cd "./$dir/"

    # Execute the build_image.sh script in the current directory
    bash "build_image.sh"

    # Return to the parent directory
    cd ..
done
