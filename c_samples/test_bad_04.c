// test_bad_04.c

int avgTwo(int a, int b) {
    return (a + b) / 2;
}

void doNothing() {
    // nothing here
}

int main() {
    int test_avg = avgTwo(10, 20);

    if (test_avg != 15) {
        return 1;
    }

    doNothing(1);

    return 0;
}