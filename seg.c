#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>

#define MAX_SIZE 100

struct node {
    struct node *next;
    int         data;
};


struct node *delete_second_last(struct node *head);
struct node *array_to_list(int len, char *array[]);
void print_list(struct node *head);
int get_list_length(struct node *head);

// DO NOT CHANGE THIS MAIN FUNCTION
int main(int argc, char *argv[]) {
    struct node *head = NULL;
    if (argc > 0) {
        head = array_to_list(argc - 1, &argv[1]);
    }
    printf("Original list: ");
    print_list(head);
    head = delete_second_last(head);
    printf("Modified list: ");
    print_list(head);
    return 0;
}


// Deletes the second last node in a linked list
// The deleted node is freed.
// The head of the list is returned.
struct node *delete_second_last(struct node *head) {
    int list_length = get_list_length(head);
    if (head == NULL || list_length == 1) {
        free(head);
        return NULL;
    }

    struct node *current = head;
    while (current->next->next != NULL) {
        current = current->next;
    }

    free(current->next);
    current->next = current->next->next;

    return head;
}

// DO NOT CHANGE THIS FUNCTION
// create linked list from array of strings
struct node *array_to_list(int len, char *array[]) {
    struct node *head = NULL;
    int i = len - 1;
    while (i >= 0) {
        struct node *n = malloc(sizeof(struct node));
        assert(n != NULL);
        n->next = head;
        n->data = atoi(array[i]);
        head = n;
        i -= 1;
    }   
    return head;
}

// DO NOT CHANGE THIS FUNCTION
// print linked list
void print_list(struct node *head) {
    printf("[");    
    struct node *n = head;
    while (n != NULL) {
        // If you're getting an error here,
        // you have returned an invalid list
        printf("%d", n->data);
        if (n->next != NULL) {
            printf(", ");
        }
        n = n->next;
    }
    printf("]\n");
}

// DO NOT EDIT
// Gets the length of a linked lists
int get_list_length(struct node *head) {
    int length = 0;
    struct node *current = head;
    while (current != NULL) {
        length++;
        current = current->next;
    }
    return length;
}