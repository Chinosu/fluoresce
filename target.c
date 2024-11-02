#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Define a struct for an Address
struct Address {
    char city[50];
    char state[50];
};

// Define a struct for a Person
struct Person {
    char name[50];
    int age;
    struct Address address; // Nested struct
    struct Person *next;    // Pointer to the next Person (for linked list)
};

// Function to create a new Person node
struct Person* createPerson(const char *name, int age, const char *city, const char *state) {
    struct Person *newPerson = (struct Person *)malloc(sizeof(struct Person));
    if (newPerson == NULL) {
        printf("Memory allocation failed.\n");
        exit(1);
    }
    strcpy(newPerson->name, name);
    newPerson->age = age;
    strcpy(newPerson->address.city, city);
    strcpy(newPerson->address.state, state);
    newPerson->next = NULL;
    return newPerson;
}

// Function to add a Person to the front of the linked list
void addPerson(struct Person **head, struct Person *newPerson) {
    newPerson->next = *head;
    *head = newPerson;
}

// Function to print the list of Persons
void printList(struct Person *head) {
    struct Person *current = head;
    while (current != NULL) {
        printf("Name: %s, Age: %d, City: %s, State: %s\n",
               current->name, current->age, current->address.city, current->address.state);
        current = current->next;
    }
}

// Function to free the linked list memory
void freeList(struct Person *head) {
    struct Person *current = head;
    struct Person *temp;
    while (current != NULL) {
        temp = current;
        current = current->next;
        free(temp);
    }
}

int main() {
    struct Person *head = NULL; // Initialize the linked list head to NULL
    int pi = 3;
    int *pi_ref = &pi;
    printf("%x %ls\n", pi, pi_ref);
    // Create new Person nodes
    struct Person *person1 = createPerson("Alice", 28, "New York", "NY");
    struct Person *person2 = createPerson("Bob", 34, "Los Angeles", "CA");
    struct Person *person3 = createPerson("Charlie", 23, "Chicago", "IL");

    // Add Persons to the linked list
    addPerson(&head, person1);
    addPerson(&head, person2);
    addPerson(&head, person3);

    // Print the linked list
    printf("Linked List of Persons:\n");
    printList(head);

    // Free the linked list memory
    freeList(head);

    return 0;
}
