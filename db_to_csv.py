import csv
import os

def get_list_books(cursor):
    """ The list of book titles typed correctly is located in the table BOOK_INFO. This function returns a nest list.
    The items of this list are lists that contain the book ids and the titles of the books that are printed to
    the user. """
    cursor.execute('SELECT id, title FROM BOOK_INFO')
    all_books = cursor.fetchall()
    return [[book_id, book_name] for (book_id, book_name) in all_books]


def get_all_words_specific_book(cursor, book_id):
    """ Knowing the book id, returns a nested list. The items of the list are lists that contain the highlighted words
     in the book and the context sentence in which this word is found. """
    book_id_tuple = (book_id,)
    cursor.execute("SELECT word_key, usage FROM LOOKUPS WHERE book_key=?", book_id_tuple)
    list_words_sentences = cursor.fetchall()
    # This step removes the "en:" or "de:" before each word.
    list_words_sentences_without_en = [[words[3:], sentences]
                                       for [words, sentences] in list_words_sentences]
    return list_words_sentences_without_en


def main(cursor):
    print("The list of books with highlighted content in your Kindle include the following books:")
    my_books = get_list_books(cursor)
    for book in my_books:
        print(f"{my_books.index(book)}: {book[1]}")

    print(f"Please type a number between 0 and {len(my_books) - 1} to generate the CSV file.")
    user_input_number = int(input())
    selected_book_id = my_books[user_input_number][0]

    # Write the words and sentences in a CSV file.
    with open("words_and_sentences.csv", "w") as words_and_sentences:
        writer = csv.writer(words_and_sentences)
        for line in get_all_words_specific_book(cursor, selected_book_id):
            writer.writerow(line)


def create_csv(cursor, application, book_index, book_title):
    my_books = get_list_books(cursor)
    selected_book_id = my_books[book_index][0]

    # Write the words and sentences in a CSV file.
    with open(os.path.join(application.instance_path, 'csv_files', f'vocab_{book_title}.csv'), "w") as words_and_sentences:
        writer = csv.writer(words_and_sentences)
        for line in get_all_words_specific_book(cursor, selected_book_id):
            writer.writerow(line)


# if __name__ == "__main__":
#     """ This is executed when run from the command line """
#     main(cursor)



# def get_all_words_with_context():
#     c.execute("SELECT word_key, usage FROM LOOKUPS")
#     return c.fetchall()

# for book in get_list_books():
#     print(book)
#
# for word in get_all_words_specific_book('How_to_Change_Your_Mind:B7DE3B75'):
#     print(word)
#




