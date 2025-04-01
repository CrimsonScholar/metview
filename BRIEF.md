# Readme
Here at Art Corporation Inc. we care deeply amount the power that Art has on us.

Our users are always looking for a way to explore the work of artists from all around the world.
It would be great if we could offer them a bit of software to guide them to freely search and find such artworks.

Luckily, the MET allows free access to their Database via a REST API.
The endpoints for this API are documented at https://metmuseum.github.io .

All of our users are very technologically savvy and love using Mac-idiomatic user interfaces,
so to solve this problem we ask you to develop a graphical user interface (GUI) that runs on macOS.

## Requirements

No matter what you choose as technology, we'll want our users to be able to:
- Search works by their MET 'classification' (e.g.: Etchings, Prints)
- Refine the search by only listing works that have an image
- Customize whether works should be displayed by ascending or descending date of creation

Your application should provide the following affordances to users:
- Search
- Image preview (for works that have an image)
- Metadata display, you have free choice on what data to display and how

For the purpose of this exercise, you should only return the FIRST 80 objects returned by the MET REST API.
So if a particular query returns 50_000 results, we want to only display the first 80 to the user.

### Output

You final product should be an application bundle that is compatible with macOS Sonoma.
If you decide to use Python, please make use of one of the many available tools to create
such a bundle from a Python package.

## Bonus Points

- Performance is important, so we'll appreciate any optimization that doesn't let our users wait around for too long after a search is initiated.
- For us, the commit history is a work of art just like a print, so try to keep it tidy.
- Anything else you can think of that would improve the UX.

## Limitations

### Language

You are free to write your solution in any of these programming languages and GUI frameworks:
- Swift, with SwiftUI, AppKit or Mac Catalyst
- Python 3, with PySide 2 or PySide 6

Please use English for all the comments and documentation.
