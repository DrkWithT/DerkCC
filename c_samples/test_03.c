// test_03.c
// Added by DrkWithT

int maxOfTwo(int a, int b) {
    if (a < b) {
        return b;
    } else {
        return a;
    }
}

int main() {
    int something_big = maxOfTwo(420, 69);
    return 0;
}