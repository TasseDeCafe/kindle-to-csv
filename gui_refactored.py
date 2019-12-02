from pathlib import Path
import sqlite3
import csv
import sys

if sys.version_info[0] >= 3:
    import PySimpleGUI as sg
else:
    import PySimpleGUI27 as sg


# The list of book titles typed correctly is located in the table BOOK_INFO. This function returns a nest list.
# The items of this list are lists that contain the book id numbers and the title of the books that are printed to the
# user.


def get_list_books(**kwargs):
    """ The list of book titles typed correctly is located in the table BOOK_INFO. This function returns a nest list.
    The items of this list are lists that contain the book ids and the titles of the books that are printed to
    the user. """
    # Connect to the database
    connection = sqlite3.connect(kwargs['path_database'])
    c = connection.cursor()
    c.execute('SELECT id, title FROM BOOK_INFO')
    all_books = c.fetchall()
    # In the Kindle database, the books are identified with a unique ID and the title of the book.
    return {book_name: book_id for (book_id, book_name) in all_books}


def get_all_words_specific_book(**kwargs):
    """ Knowing the book id, returns a nested list. The items of the list are lists that contain the highlighted words
     in the book and the context sentence in which this word is found. """
    all_book_names = get_list_books(**kwargs)
    book_id = all_book_names[kwargs['selected_book']]
    # The book IDs must be in a tuple for the SQL request.
    book_id_tuple = (book_id,)
    connection = sqlite3.connect(kwargs['path_database'])
    c = connection.cursor()
    c.execute("SELECT word_key, usage FROM LOOKUPS WHERE book_key=?", book_id_tuple)
    list_words_sentences = c.fetchall()
    # This step removes the "en:" or "de:" before each word.
    list_words_sentences_without_en = [[words[3:], sentences]
                                       for [words, sentences] in list_words_sentences]
    return list_words_sentences_without_en


def generate_csv_file(**kwargs):
    """ Write the words and sentences in a CSV file. """
    all_words_sentences = get_all_words_specific_book(**kwargs)
    with open(f"words_and_sentences_{kwargs['selected_book']}.csv", "w") as csv_file_with_words_sentences:
        writer = csv.writer(csv_file_with_words_sentences)
        for line in all_words_sentences:
            writer.writerow(line)


def window_layout():
    """ Layout for the GUI window. """
    layout = [
        [sg.Text('Please browse to the path of the vocab.db file on your Kindle:')],
        [sg.Input(key='database_field'), sg.FileBrowse()],
        [sg.Button('Show list of books in the Kindle'), sg.Cancel()],
        [sg.Text('Error: please select the file vocab.db in your Kindle.', visible=False, key='database_error_message',
                 text_color='red')],
        [sg.DropDown(values='', key='selected_book', size=(60, 6))],
        [sg.Button(button_text='Generate the CSV file'), sg.Exit()],
        [sg.Text('The CSV file has been generated successfully.', visible=False, key='file_generated_success',
                 text_color='green')],
        [sg.Text('Whoops, that didn\'t work, please try again.', visible=False, key='file_generated_error',
                 text_color='green')]
    ]
    return layout

# Buttons functions:


def button_show_list_books(**kwargs):
    """ The 'Show list of books in the Kindle' button fills the dropdown menu with the book titles from the Kindle. """
    if kwargs['database_field']:
        my_books = get_list_books(**kwargs)
        kwargs['window'].FindElement(key='selected_book').Update(values=[key for key in my_books.keys()])


def button_cancel(**kwargs):
    """ The cancel button empties the database field, the dropdown menu and hides the error message. """
    kwargs['window'].FindElement(key='selected_book').Update(values='')
    kwargs['window'].FindElement(key='database_field').Update(value='')
    kwargs['window'].FindElement(key='database_error_message').Update(visible=False)


def button_generate_csv(**kwargs):
    """ The 'Generate the CSV file' button generates the CSV file and prints a message if the operation
     has succeeded or not."""
    # Will execute if the database field is not empty.
    if kwargs['database_field']:
        selected_book = kwargs['selected_book']
        generate_csv_file(**kwargs)
        generated_file = Path(f'/words_and_sentences_{selected_book}.csv')
        # Checks if the CSV file has been generated.
        if generated_file:
            kwargs['window'].FindElement(key='file_generated_success').Update(visible=True)
        else:
            kwargs['window'].FindElement(key='file_generated_error').Update(visible=True)

# the functions are stored in the values of a dictionary. This allows the button functions to be called with a single
# line in the main() function.


button_functions = {'Show list of books in the Kindle': button_show_list_books,
                    'Cancel': button_cancel,
                    'Generate the CSV file': button_generate_csv
                    }


def database_error(**kwargs):
    """ Shows the database error message. """
    kwargs['window'].FindElement(key='database_error_message').Update(visible=True)
    # Empties the dropdown menu.
    kwargs['window'].FindElement(key='selected_book').Update(values='')


def main():
    # Initializes the window with PySimpleGUI.
    window = sg.Window('Kindle to CSV', window_layout())
    while True:
        event, values = window.Read()
        # If there are no events, values or if the user clicks on exit, break out of the loop
        if event in ('Exit', None) or not values:
            break
        # Keyword arguments of the functions. The keys of "values" is given by the layout.
        kwargs = {'path_database': values['Browse'],
                  'database_field': values['database_field'],
                  'selected_book': values['selected_book'],
                  'window': window
                  }
        # Hides the error messages before an event.
        window.FindElement(key='file_generated_success').Update(visible=False)
        window.FindElement(key='database_error_message').Update(visible=False)

        # If the database input field is empty, print the database error message.
        if not kwargs['database_field']:
            database_error(**kwargs)
        try:
            # This function takes a function as a parameter. The parameter is one of the button functions.
            button_functions[event](**kwargs)
        # If the user selected a file that is not a database or the wrong database, print the database error message.
        except (sqlite3.DatabaseError, sqlite3.DataError, sqlite3.OperationalError):
            database_error(**kwargs)
    window.Close()


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
