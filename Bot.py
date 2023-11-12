import shlex
from Contacts import AddressBook, Record, DuplicatedPhoneError
from Notes import Notes, Note
from Serialization import SerializationContext
from Suggestions import Suggester



EXIT_COMMANDS = {"good bye", "bye", "exit", "quit", "stop"}
GREET_COMMANDS = {"hi", "hey", "hello", "howdy", "hi-ya", "howdy-do", "good morning", "good afternoon"}
GREETING_RESPONSES = {
    1: "Hello! How can I help you?",
    2: "Hey again! So how can I help you?",
    3: "Hey! Are you dumb or what? How can I help you?",
    4: "Are you kidding me? We have greeted 3 time now. Can I help you somehow?",
    5: "Fuuuck! Are you all right?",
    6: "Gotha, you might have Down syndrom... Hello, lovely human being :)",
    7: "Hellooo :)"
}

records: AddressBook = None
notes: Notes = None

def input_error(*expected_args):
    def input_error_wrapper(func):
        def inner(*args):
            try:
                return func(*args)
            except IndexError:
                return f"Please enter {' and '.join(expected_args)}"
            except KeyError:
                return f"The record for contact {args[0]} not found. Try another contact or use help."
            except ValueError as error:
                if error.args:
                    return error.args[0]
                return f"Phone format '{args[1]}' is incorrect. Use digits only for phone number."
            except DuplicatedPhoneError as phone_error:
                return f"Phone number {phone_error.args[1]} already exists for contact {phone_error.args[0]}."
            except AttributeError:
                return f"Contact {args[0]} doesn't have birthday yet."
        return inner
    return input_error_wrapper

def capitalize_args(*indexes):
    def capitalize(func):
        def inner(*args):
            new_args = list(args)
            for idx in indexes:
                new_args[idx] = new_args[idx].lower().title()
            return func(*new_args)
        return inner
    return capitalize

def unknown_handler (*words):
    suggester = Suggester(words[0])
    def inner(*args) -> str:        
        suggestion = suggester.suggest(args[0]) or ""
        if suggestion:      
            sug_command = f"{suggestion} {' '.join(*args[1:])}".strip()   

            return (f"Unknown command. Did you mean '{sug_command}'", sug_command)
        return f"Unknown command. Use help: \n{help_handler()(*args)}"
    return inner

def help_handler():
    help_txt = ""
    def inner(*args) -> str:
        nonlocal help_txt
        if not help_txt:
            with open("help.txt") as file:            
                help_txt = "".join(file.readlines())
        return help_txt
    return inner

@capitalize_args(0)
@input_error("name", "phone")
def add_handler(*args) -> str:
    user_name = args[0]
    user_phones = args[1:]
    record = records.find(user_name, True)
    if not record:
        record = Record(user_name)
        for user_phone in user_phones:
            record.add_phone(user_phone)
        records.add_record(record)
        return f"New record added for {user_name} with phone number{'s' if len(user_phones) > 1 else ''}: {'; '.join(user_phones)}."
    else:
        response = []
        for user_phone in user_phones:
            record.add_phone(user_phone)
            response.append(f"New phone number {user_phone} for contact {user_name} added.")
        return "\n".join(response)

@input_error("title", "text")
def note_handler(*args) -> str:
    note_title = args[0]
    note_text = " ".join(args[1:])
    note: Note = notes[note_title]
    if note_text:
        if not note:
            note = Note(note_title, note_text)
            notes.add_note(note)
            return f"New note added with title '{note_title}' and text '{note_text}'."
        else:
            notes.edit_note(note_title, note_text)        
            return f"Note with title '{note_title}' updated to '{note_text}'."
    elif note:
        return f"{note}"
    return f"Note with title '{note_title}' already exists"

@capitalize_args(0)
@input_error("name", "old_phone", "new_phone")
def change_handler(*args) -> str:
    user_name = args[0]
    old_phone = args[1]
    new_phone = args[2]
    record = records.find(user_name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return f"Phone number for {user_name} changed from {old_phone} to {new_phone}."

@capitalize_args(1)
@input_error("entity","name|title")
def delete_handler(*args) -> str:
    first_arg = 0
    if args[0].lower() == "note":
        first_arg = 1
        note_title = args[first_arg]
        if notes.delete_note(note_title):
            return f"Note with title '{note_title}' deleted."
        return f"Note with title '{note_title}' not found."
    
    elif args[0].lower() == "contact":
        first_arg = 1
    else:
        first_arg = 0
    
    user_name = args[first_arg]
    user_phones = args[first_arg+1:]

    if len(user_phones) >= 1:
        record = records.find(user_name)
        if record:
            response = []
            for user_phone in user_phones:
                record.remove_phone(user_phone)
                response.append(f"Phone number {user_phone} for contact {user_name} removed.")
            return "\n".join(response)
    else:
        if records.delete(user_name):
            return f"Record for contact {user_name} deleted."
        return f"Record for contact {user_name} not found."

@capitalize_args(0)    
@input_error("name")
def birthday_handler(*args) -> str:
    user_name = args[0]
    user_birthday = args[1] if len(args) > 1 else None
    record = records.find(user_name)
    if record:
        if user_birthday:
            record.add_birthday(user_birthday)
            return f"Birthday {user_birthday} for contact {user_name} added."
        else:
            return f"{record.days_to_birthday()} days to the next {user_name}'s birthday ({record.birthday})."

@input_error([])
def greet_handler(num: int) -> str:
    def inner_greet(*args):
        nonlocal num
        num = num + 1 if num < 7 else 7
        return GREETING_RESPONSES[num]
    return inner_greet

@capitalize_args(0)
@input_error("name")
def phone_handler(*args) -> str:
    user_name = args[0]
    record = records.find(user_name)
    if record:
        return "; ".join(map(lambda phone: str(phone), record.phones))    
    return f"Record for contact {user_name} not found."

@input_error("entity", "term")
def search_handler(*args) -> str:
    entity = args[0]
    term = ""
    if entity == "notes":
        term = " ".join(args[1:])
        result = notes.search_notes(term)   
        if result:
            return result 
        return f"No notes found for '{term}' tag."
    elif entity == "contacts":
        term = args[1]
    else:
        term = args[0]
    contacts = records.search_contacts(term)
    if contacts:
        return "\n".join(map(lambda contact: str(contact), contacts))    
    return f"No contacts found for '{term}'."

@input_error([])
def show_handler(*args) -> str:
    if not args:
        return records.iterator() 
    if args[0] == "contacts":
        return records.iterator()   
    if args[0] == "notes":
        return notes.iterator()
    if args[0] == "birthdays":
        days = args[1]
        return records.get_contacts_by_birthdays(int(days))
    return records.iterator() 

COMMANDS = {
    "add": add_handler,
    "change": change_handler,
    "phone": phone_handler,
    "show": show_handler,
    "greet": greet_handler(0),
    "delete": delete_handler,
    "birthday": birthday_handler,
    "search": search_handler,
    "note": note_handler,
    "help": help_handler(),    
}

UNKNOWN_COMMAND = unknown_handler(set(COMMANDS.keys()).union(GREET_COMMANDS, EXIT_COMMANDS))

def command_parser(input:str) -> tuple:
    clauses = []
    command = ""
    args = []
    if input.lower() in GREET_COMMANDS:
        command = "greet" 
    else:
        clauses = shlex.split(input)
        if clauses:
            command = clauses[0]              
            if len(clauses) > 0:
                args = clauses[1:]
    if command.lower() in COMMANDS.keys():
        return COMMANDS[command.lower()], args
    
    return UNKNOWN_COMMAND, (command.lower(), args)

def process_input(user_input: str):
    user_input = user_input.strip()
    if user_input in EXIT_COMMANDS:
        return "<break>"    
    func, data = command_parser(user_input)
    result = func(*data)
    if isinstance(result, str):
        print(result)
    elif isinstance(result, tuple):
        print(result[0])
        print("Type 'yes' or 'y' to run the suggested command or press enter to skip.")
        answer = input(">>> ")
        if answer.lower() in ('yes', 'y'):                    
            return process_input(result[1])
    else:
        for i in result:                
            print ("\n".join(i))
            input("Press enter to show more records")     

def main():
    global records, notes
    with SerializationContext(AddressBook("address_book.pkl"), Notes("notes.pkl")) as context:
        records = context[AddressBook]        
        notes = context[Notes]        
        while True:
            user_input = input(">>> ")            
            if process_input(user_input) == "<break>":
                print("Good bye!")
                break      


if __name__ == "__main__":
    main()