
# Update all pip libraries

for i in ` pip3 list | awk -F ' ' ' {print $1}' `
do
    echo $i
    pip3 install --upgrade $i
done
