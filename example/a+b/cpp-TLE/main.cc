#include <iostream>

using namespace std;

int main() {
  int a, b;
  cin >> a >> b;
  int c = 0;
  for (int i = 0; i < a; ++i) {
    c++;
  }
  for (int i = 0; i < b; ++i) {
    c++;
  }
  cout << c << endl;
  return 0;
}
