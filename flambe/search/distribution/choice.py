from typing import List, Any, Optional, Union, Dict

import numpy as np

from flambe.search.distribution.distribution import Distribution


PRIMITIVES = (int, float, bool, str, list, tuple, set, dict)


class Choice(Distribution, tag_override="~c"):
    """A discrete choice distribution."""

    def __init__(self,
                 options: Union[List, Dict[str, Any]],
                 probs: Optional[List[float]] = None):
        """Initialize the distribution.

        Parameters
        ----------
        choices: List
            The list of possible values to take.
        probs: List[float]
            List of probabilities for the corresponding choices.

        """
        if isinstance(options, dict):
            named_options = list(options.items())
            options = [opt for _, opt in options.items()]
        elif all(type(opt) in PRIMITIVES for opt in options):
            named_options = [(str(opt), opt) for opt in options]
        else:
            raise ValueError("Choices over non built-in types must be provided with a name.")

        self.options = options
        self.named_options = named_options
        self.n_options = len(options)
        if probs is None:
            self.probs = np.array([1 / len(options)] * len(options))
        else:
            self.probs = np.array(probs)

    @classmethod
    def from_sequence(cls, args) -> 'Choice':
        """Build the distribution from positonal arguments."""
        return cls(args)  # type: ignore

    def sample(self) -> Any:
        """Sample from the categorical distribution.

        Returns
        -------
        Any
            An option sampled from the multinomial.

        """
        index = np.random.choice(list(range(self.n_options)), p=self.probs)
        return self.options[index]

    def option_to_int(self, option: Any) -> int:
        """Convert the option to a categorical integer.

        Parameters
        ----------
        option: Any
            One of the possible choices for the variable.

        Returns
        -------
        int
            The index of that option in the list.

        """
        idx = np.where(self.options == option)[0]
        if len(idx) == 0:
            raise ValueError('Value not found in choices!')
        else:
            return idx[0]

    def int_to_option(self, index: int) -> Any:
        """Convert a categorical integer to a choice.

        Parameters
        ----------
        index: int
            A value in {0, ..., n_choices-1}.

        Returns
        -------
        Any
            The option at the index.

        """
        return self.options[index]

    def __getitem__(self, key):
        """Iterate through the options."""
        return self.options[key]

    def __iter__(self):
        """Iterate through the options."""
        yield from list(self.options)

    def __len__(self):
        """Get the number of options."""
        return len(self.options)
