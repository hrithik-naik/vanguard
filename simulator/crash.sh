for i in {1..5}; do
    ./crash_test || echo "crashed $i"
    sleep 1
done
