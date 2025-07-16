# load hf key and set cache dir
from dotenv import load_dotenv
load_dotenv()

import torch.nn.functional as F
import torch
from transformers import AutoTokenizer, AutoModel, AutoModelForSequenceClassification


class GteMultilingualBase():
    """
    A wrapper class for the 'Alibaba-NLP/gte-multilingual-base' embedding model.

    Attributes:
        device (torch.device or str): The device on which to load the model (e.g., 'cuda', 'cpu').
        dtype (torch.dtype): The data type for model computations (default: torch.bfloat16).
        tokenizer (AutoTokenizer): The tokenizer associated with the GTE model.
        model (AutoModel): The loaded GTE-Multilingual-Base model.
    """
    
    def __init__(self, device, dtype=torch.bfloat16):
        """
        Initializes the GteMultilingualBase model.

        Args:
            device (torch.device or str): The device to load the model onto (e.g., 'cuda', 'cpu').
            dtype (torch.dtype, optional): The data type for model operations. Defaults to torch.bfloat16.
        """
        
        self.device = device
        self.dtype = dtype
        
        model_id = 'Alibaba-NLP/gte-multilingual-base'
        
        # Load the tokenizer specific to the embedding model.
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        # Load the pre-trained GTE-Multilingual-Base model.
        self.model = AutoModel.from_pretrained(
            model_id, 
            trust_remote_code=True,  # Allows loading custom code from the model's repository.
            torch_dtype=dtype,       # Sets the data type for model parameters and computations.
            unpad_inputs=True,       # Optimizes for unpadded inputs if applicable.
            use_memory_efficient_attention=True, # Leverages memory-efficient attention mechanisms.
        ).to(device)  # Move the model to the specified device.

    def embed(self, texts):
        """
        Generates embeddings for a list of text strings.

        Args:
            texts (list[str]): A list of text strings to embed.

        Returns:
            torch.Tensor: A tensor of shape (batch_size, embedding_dim)
                          containing the normalized embeddings for the input texts.
        """

        # Tokenize the input texts, ensuring proper padding, truncation, and tensor conversion.
        batch_tokens = self.tokenizer(
            texts, 
            max_length=8192,         # Maximum sequence length for tokenization.
            padding='longest',       # Pad to the length of the longest sequence in the batch.
            truncation=True,         # Truncate sequences longer than max_length.
            return_tensors='pt'      # Return PyTorch tensors.
        ).to(self.device)            # Move tokens to the specified device.

        with torch.no_grad(): # Disable gradient calculation for inference to save memory and speed up computation.
            output = self.model(**batch_tokens)
            
        # Extract the embeddings from the CLS token (first token) of the last hidden state.
        embeddings = output.last_hidden_state[:, 0]
        # Normalize the embeddings to unit length (L2 normalization).
        embeddings = F.normalize(embeddings, p=2, dim=1)
        
        return embeddings
    
    
class SnowflakeArcticEmbedMV2_0():
    """
    A wrapper class for the 'Snowflake/snowflake-arctic-embed-m-v2.0' embedding model.


    Attributes:
        device (torch.device or str): The device on which to load the model.
        dtype (torch.dtype): The data type for model computations (default: torch.bfloat16).
        tokenizer (AutoTokenizer): The tokenizer for the Snowflake Arctic Embed model.
        model (AutoModel): The loaded Snowflake Arctic Embed M v2.0 model.
    """

    def __init__(self, device, dtype=torch.bfloat16, compile=False):
        """
        Initializes the SnowflakeArcticEmbedMV2_0 model.

        Args:
            device (torch.device or str): The device to load the model onto.
            dtype (torch.dtype, optional): The data type for model operations. Defaults to torch.bfloat16.
            compile (bool, optional): Whether to compile the model's forward pass using `torch.compile`
                                      for potential performance improvements. Defaults to False.
        """
        
        self.device = device
        self.dtype = dtype
        
        model_id = 'Snowflake/snowflake-arctic-embed-m-v2.0'
        
        # Load the tokenizer specific to the embedding model.
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        # Load the pre-trained Snowflake Arctic Embed M v2.0 model.
        model = AutoModel.from_pretrained(
            model_id, 
            trust_remote_code=True,      # Allows loading custom code from the model's repository.
            torch_dtype=dtype,           # Sets the data type for model parameters and computations.
            unpad_inputs=True,           # Optimizes for unpadded inputs if applicable.
            device_map={'': device},     # Maps the model to the specified device.
            add_pooling_layer=False,     # Prevents adding an extra pooling layer if not needed.
            use_memory_efficient_attention=True, # Leverages memory-efficient attention mechanisms.
        )
        self.model = model
        # Compile the model's forward pass if `compile` is True.
        if compile:
            model.forward = torch.compile(self.model.forward)

    def embed(self, texts):
        """
        Generates embeddings for a list of text strings using the Snowflake Arctic Embed model.

        Args:
            texts (list[str]): A list of text strings to embed.

        Returns:
            torch.Tensor: A tensor of shape (batch_size, embedding_dim)
                          containing the normalized embeddings.
        """
        
        # Tokenize the input texts with specified parameters.
        batch_tokens = self.tokenizer(
            texts, 
            max_length=8192, 
            padding='longest', 
            truncation=True, 
            return_tensors='pt'
        ).to(self.device) # Move tokens to the specified device.

        # Disable gradient calculation and ensure operations are on the correct CUDA device.
        with torch.no_grad(), torch.cuda.device(self.device):      
            output = self.model(**batch_tokens)

            # Extract and normalize the embeddings.
            embeddings = output.last_hidden_state[:, 0]
            embeddings = F.normalize(embeddings, p=2, dim=1)

        return embeddings


class JinaEmbeddingsV3TextMatching():
    """
    A wrapper class for the 'jinaai/jina-embeddings-v3' model, specifically
    configured for 'text-matching' tasks.

    Attributes:
        device (torch.device or str): The device on which to load the model.
        dtype (torch.dtype): The data type for model computations (default: torch.bfloat16).
        model (AutoModel): The loaded Jina Embeddings V3 model.
    """

    def __init__(self, device, dtype=torch.bfloat16, model_id=None):
        """
        Initializes the JinaEmbeddingsV3TextMatching model.

        Args:
            device (torch.device or str): The device to load the model onto.
            dtype (torch.dtype, optional): The data type for model operations. Defaults to torch.bfloat16.
        """
        
        self.device = device
        self.dtype = dtype
        
        if model_id is None:
            model_id = 'jinaai/jina-embeddings-v3'
        
        # Load the Jina Embeddings V3 model.
        self.model = AutoModel.from_pretrained(
            model_id, 
            trust_remote_code=True,   # Allows loading custom code from the model's repository.
            torch_dtype=torch.bfloat16, # Specifically set dtype to bfloat16 for this model.
        ).to(device) # Move the model to the specified device.

    def embed(self, texts):
        """
        Generates embeddings for a list of text strings using the Jina Embeddings V3 model
        with a 'text-matching' task.
        Args:
            texts (list[str]): A list of text strings to embed.

        Returns:
            torch.Tensor: A tensor of shape (batch_size, embedding_dim)
                          containing the embeddings.
        """
        
        with torch.no_grad(): # Disable gradient calculation for inference.
            # Use the model's built-in encode method with 'text-matching' task.
            output = self.model.encode(texts, task='text-matching')
            
        # Convert the output (which might be a numpy array or list) to a PyTorch tensor
        # and move it to the specified device and data type.
        embeddings = torch.tensor(output).to(self.device, self.dtype)
        
        return embeddings


class BERTEmbeddings():
    """
    A wrapper class for the 'bert models' embedding model.


    Attributes:
        device (torch.device or str): The device on which to load the model.
        dtype (torch.dtype): The data type for model computations (default: torch.bfloat16).
        tokenizer (AutoTokenizer): The tokenizer for the Snowflake Arctic Embed model.
        model (AutoModel): The loaded Snowflake Arctic Embed M v2.0 model.
    """

    def __init__(self, device, dtype=torch.bfloat16, compile=False, model_id=None):
        """
        Initializes the BERTEmbeddings model.

        Args:
            device (torch.device or str): The device to load the model onto.
            dtype (torch.dtype, optional): The data type for model operations. Defaults to torch.bfloat16.
            compile (bool, optional): Whether to compile the model's forward pass using `torch.compile`
                                      for potential performance improvements. Defaults to False.
        """
        
        self.device = device
        self.dtype = dtype
        
        if model_id is None:
            model_id = 'UBC-NLP/ARBERT'
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModel.from_pretrained(
            model_id
        ).to(device)

    def embed(self, texts):
        batch_tokens = self.tokenizer(
            texts, 
            max_length=512, 
            padding='longest', 
            truncation=True, 
            return_tensors='pt'
        ).to(self.device) # Move tokens to the specified device.

        # Disable gradient calculation and ensure operations are on the correct CUDA device.
        with torch.no_grad(), torch.cuda.device(self.device):      
            output = self.model(**batch_tokens)

            # Extract and normalize the embeddings.
            embeddings = output.last_hidden_state[:, 0]
            embeddings = F.normalize(embeddings, p=2, dim=1)

        return embeddings 
    
def get_embedder_instance(model_id, device, dtype = torch.bfloat16):
    """
    Factory function to get an instance of a specified embedding model.

    This function dynamically creates an instance of the appropriate embedding
    model class based on the provided `model_id`. This allows for flexible
    selection and instantiation of different embedding models, which is crucial
    for evaluating and comparing various multilingual embedding approaches
    as might be done in the research presented in the associated paper.

    Args:
        model_id (str): The identifier of the embedding model to instantiate.
                        Supported IDs include:
                        - 'Alibaba-NLP/gte-multilingual-base'
                        - 'Snowflake/snowflake-arctic-embed-m-v2.0'
                        - 'jinaai/jina-embeddings-v3'
        device (torch.device or str): The device to load the model onto.
        dtype (torch.dtype): The data type for model operations.

    Returns:
        Union[GteMultilingualBase, SnowflakeArcticEmbedMV2_0, JinaEmbeddingsV3TextMatching]:
            An instance of the requested embedding model class.

    Raises:
        ValueError: If an unknown `model_id` is provided.
    """
    print(model_id)
    if model_id == 'Alibaba-NLP/gte-multilingual-base':
        embedder_class = GteMultilingualBase
    
    elif model_id == 'Snowflake/snowflake-arctic-embed-m-v2.0':
        embedder_class = SnowflakeArcticEmbedMV2_0
    
    elif model_id == 'jinaai/jina-embeddings-v3':
        embedder_class = JinaEmbeddingsV3TextMatching
    
    elif 'bert' in model_id.lower():
        embedder_class = BERTEmbeddings
    
    
    else:
        raise ValueError(f"Unknown model ID: {model_id}")
    
    return embedder_class(device, dtype)