README: Code can be run via "python eigenface.py". Alternatively, the module
        can be imported and individual functions run/tested there, though the
        former method is suggested beacuse a lot of code is in the module main.

        Dependencies are matplotlib, scipy, numpy >= 1.9, sklearn, and a modern
        python platform installed. Practically speaking though, plotting code
        can be commented out, and scipy isn't being used in the present
        implementation, so the practical dependencies are sklearn and numpy.

        Any questions can be directed to chstan@stanford.edu or
        dwang22@stanford.edu.

        The hardest part of the problem was probably dealing with the
        computational constraints imposed by the high dimensionality of the
        problem, and understanding exactly how the network construction happens
        in the paper. For some reason, they take an unnecessary amount of time
        explaining how to take a mean, and none on this, even though it does
        not seem to be a standard mathematical construction!
