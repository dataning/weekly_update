
#analogy 

Joe Armstrong, a leading computer scientist and the inventor of the computer lan- guage Erlang, uses an effective metaphor for the lack of separation between the object of interest and its environment: You wanted a banana but what you got was a gorilla holding the banana and the entire jungle [Seibel, 2009].

----

Joe Armstrong's metaphor about the lack of separation between an object of interest and its environment highlights a common issue in software design and system architecture. Here’s a breakdown of the metaphor and its implications:

### The Metaphor:
- **Banana**: Represents the specific, desired component or feature you want.
- **Gorilla**: Represents the larger, unintended component that comes along with the desired feature.
- **Entire Jungle**: Symbolizes the entire system or environment that gets entangled with the component you wanted.

### Explanation:
When Armstrong says, "You wanted a banana but what you got was a gorilla holding the banana and the entire jungle," he means that when you try to extract or utilize a particular feature or component (the banana), you often end up getting much more than you intended. This includes other components (the gorilla) and their dependencies or context (the entire jungle).

### Implications in Software Design:
1. **Tight Coupling**: This metaphor underscores the issue of tight coupling in software systems. Tight coupling occurs when components are heavily dependent on each other, making it difficult to isolate and use individual parts without involving many other parts of the system.
   
2. **Complex Dependencies**: It highlights how complex dependencies can make it challenging to extract or utilize a single feature without bringing in a lot of additional, possibly unnecessary, parts of the system.

3. **System Overhead**: The metaphor also points out the potential overhead and bloat in systems where extracting a small piece requires dealing with a much larger system.

### Practical Example:
Imagine you need a specific library function from a large software library. Ideally, you would want just that function (the banana). However, to use it, you might need to include the entire library with all its dependencies (the gorilla and the jungle), which could be overkill and add unnecessary complexity to your project.

### Conclusion:
Joe Armstrong's metaphor is a vivid way to describe the problem of unnecessary complexity and dependencies in software systems. It emphasizes the importance of designing systems with clear separation of concerns and minimizing dependencies, allowing developers to work with specific components without being forced to handle the entire system.