BibTeX Normalization Tool

format, normalize and check bibtex files

Functionalities:
1) select cited entries from multiple .bib files (-c .aux)
  1.1) output all cited entries into one file (-o .bib) 
  1.2) uncited entries are stored in file notcited.bib
2) unify format of all entries
  example output:
    @article{greenwade93,
        author     = {George D. Greenwade},
        title      = {The {C}omprehensive {T}ex {A}rchive {N}etwork ({CTAN})},
        year       = {1993},
        journal    = {TUGBoat},
        volume     = {14},
        number     = {3},
        pages      = {342--351},
    }
3) check and correct errors for entries
