// test_04.c
// Added by DrkWithT

int main() {
    int a = 0;
    int b = 0;
    int c = 42;

    a = b = c;

    // check abc

    if (a != b && b != c) {
        return 1;
    }

    if (a != b || a != c) {
        return 1;
    }

    return 0;
}