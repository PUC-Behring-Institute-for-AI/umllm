Let's simulate a single step in a deterministic Turing machine encoded using an alphabet with seven symbols: "Q", "S", "0", "1", "L", "R", and ".".  Certain strings of these symbols are to be interpreted as follows:

1. A "Q" followed by one or more "0"s and "1"s represents a state of the simulated Turing machine.
2. A "S" followed by one or more "0"s and "1"s represents a symbol of the simulated Turing machine.
3. An "L" indicates that a movement to the left should be performed by the simulated Turing machine.
4. An "R" indicates a movement to the right should be performed by the simulated Turing machine.
5. An "." represents the blank (empty) symbol.

To perform a single step in the simulated Turing machine, we will use ten tapes:

1. The "Machine" tape, containing the transition table of the simulated Turing machine.
2. The "Work" tape, encoding the work tape of the simulated Turing machine together with the current position of its head.
3. The "State" tape, containing the current state of the simulated Turing machine.
4. The "Symbol" taped, containing the symbol being currently read by the head the simulated Turing machine.
5. The "LeftSymbol" tape, containing the symbol to the left of the symbol being currently read by the head of the simulated Turing machine.
6. The "NextState" tape, containing the next state to transition the simulated Turing machine to.
7. The "NextSymbol" tape, containing the symbol to write in place of the symbol being currently read by the head of simulated Turing machine.
8. The "NextMove" tape, containing the direction, "L" (left) or "R" (right), to move the head of the simulated Turing machine.
9. The "Subst1" tape, containing the substring of the "Work" tape which should be replaced to perform the current transition.
10. The "Subst2" tape, containing the substring which should replace "Subst1" in "Work" after the current transition is preformed.

To describe the contents of these tapes, we will use the metavariables Qs, Sw, Qy, Sz and m, which range over strings of the symbols introduced above.  More specifically:

1. Qs and Qy stand each for a single state of the simulated Turing machine ("Q" followed one or more "0"s and "1"s).
2. Sw and Sz stand each for a single symbol of the simulated Turing machine ("S" followed by "0"s and "1"s) or the blank symbol ".".
3. m stand for a movement indicator symbol ("L" or "R").

In the "Machine" tape, each transition is encoded as a string of the form QsSwQySzm specifying that if the simulated Turing machine is in state Qs reading the symbol Sw then it should replace Sw by Sz, move the head in the direction m, and transition to state Qy.

At all times, the "Work" tape contains a string of the form ".XQsY." where Qs is current state of the simulated Turing machine surrounded by possibly empty strings X and Y of symbols of the simulated Turing machine or blanks.  The symbol or blank immediately following Qs in "Work" is the symbol being currently read by the head of the simulated Turing machine.  Note that by this definition, at all times, the contents of the "Work" tape is assumed to be delimited by blanks.  This means that if a non-blank symbol is ever written over the leftmost delimiting blank in the "Work" tape, then a new blank symbol must be added to the left of the written symbol.  Similarly, if a non-blank symbol is ever written over the rightmost delimiting blank in the "Work" tape, then a new blank symbol must be added to the right of the written symbol.  This way the contents of the "Work" tape are always delimited one blank symbol on the left and another blank symbol on the right.

Initially, only the tapes "Machine" and "Work" contain symbols.  The remaining tapes are assumed to start completely empty.

To execute a single cycle of the simulated Turing machine, follow the six steps below.

* Step 1 (Load the "State" and "Symbol" tapes): Locate in the "Work" tape a substring of the form QsSw.  Then write Qs into the "State" tape and "Sw" into "Symbol" tape.

* Step 2 (Load the "LeftSymbol" tape): Locate in the "Work" tape a substring of the form SuQs.  Then write Su into the "LeftSymbol" tape.  Note that Su can be either a symbol of the simulated Turing machine or a blank symbol.

* Step 3 (Load the "NextState", "NextSymbol", and "NextMove" tapes): Locate in the "Machine" tape a substring of the form QsSwQySzm such that Qs is equal to the contents of the "State" tape and Sw is equal to the contents of the "Symbol" tape.  Then write Qy into the "NextState" tape, Sz into the "NextSymbol" tape, and m into the "NextMove" tape.

* Step 4 (Load the "Subst1" tape): Let Su be the contents of the "LeftSymbol" tape, let Qs be the contents of the "State" tape, and let Sw be the contents of the "Symbol" tape.  If the contents of the "NextMove" tape is "L", write SuQsSw into the "Subst1" tape. Otherwise, if the contents of the "NextMove" tape is "R", write QsSw into the "Subst1" tape.

* Step 5 (Load the "Subst2" tape): Let Su be the contents of the "LeftSymbol" tape, let Qy be the contents of the "NextState" tape and let Sz be the contents of the "NextSymbol" tape.  If the contents of the "NextMove" tape is "L", write QySuSz into the "Subst2" tape.  Otherwise, if the contents of the "NextMove" tape is "R", write SzQy into the "Subst2" tape.

* Step 6 (Perform the substitution): In the "Work" tape, replace the first occurrence of the contents of the "Subst1" tape by the contents of the "Subst2" tape.

Perform each cycle of the simulated Turing machine interactively.  You will be provided with the contents of the "Machine" tape and the initial contents of the "Work" tape.  You will then execute steps 1 to 6, explaining what is being done during each step.  After performing the substitution step (Step 6), you will stop and display the full contents of the "Work" tape on a new line wrapped in tags <work> and </work>.  Then wait for a command.  The command will be either "continue", to execute another cycle, or "stop", to end the execution.  Don't forget that at the and of each cycle you must display the full contents of the "Work" tape, including its delimited blanks, on a new line surrounded by the tags <work> and </work>.
