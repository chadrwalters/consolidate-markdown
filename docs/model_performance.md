# Model Performance Analysis

This document tracks the performance of different vision models over time, comparing their capabilities across different types of content.

## Latest Analysis (2024-02-01)

> **Note**: As of February 2024, we have switched our default model to **Google Gemini Pro Vision** based on its excellent balance of performance, reliability, and cost-effectiveness. While GPT-4 Vision shows marginally better performance in our tests, Gemini provides comparable quality at a better price point, making it our recommended default choice.

### Test Images
1. **Code Screenshot**: Documentation of testing procedures for OpenRouter models
2. **UI Screenshot**: Development environment showing terminal output and code editor

### Model Performance

#### GPT-4 Vision
- **Code Analysis**: 9/10 (5.41s)
  - Very structured and clear
  - Captured main purpose and context
  - Included code examples with proper formatting
  - Best overall for technical content

- **UI Analysis**: 9/10 (6.24s)
  - Excellent detail and organization
  - Captured both UI structure and content
  - Noted important details like dark mode
  - Best overall for UI description

#### Google Gemini Pro Vision
- **Code Analysis**: 8/10 (6.12s)
  - Well-organized with clear sections
  - Good attention to formatting details
  - Slightly more verbose than GPT-4
  - Strong technical understanding

- **UI Analysis**: 8.5/10 (7.45s)
  - Very detailed and well-structured
  - Caught technical details like Git branch
  - Got cut off but covered most content
  - Strong UI analysis capabilities

#### Yi Vision
- **Code Analysis**: 7/10 (6.42s)
  - Good structure and detail
  - Caught most key points
  - Got cut off at the end
  - Solid but incomplete

- **UI Analysis**: 8/10 (7.02s)
  - Clear structure and good detail
  - Good balance of UI and content description
  - Complete analysis without cutoff
  - Very competent

#### DeepInfra BLIP
- **Code Analysis**: 6/10 (5.56s)
  - Good structure but less technical detail
  - More focused on document structure than code
  - Got cut off at the end
  - Decent but less technical depth

- **UI Analysis**: 7/10 (7.56s)
  - Good basic structure
  - Caught numerical details in the table
  - Less detail on UI elements
  - Solid but less detailed than others

### Speed Comparison
- **Code Screenshot**:
  1. GPT-4: 5.41s
  2. BLIP: 5.56s
  3. Gemini: 6.12s
  4. Yi: 6.42s

- **UI Screenshot**:
  1. GPT-4: 6.24s
  2. Yi: 7.02s
  3. Gemini: 7.45s
  4. BLIP: 7.56s

### Overall Rankings
1. **GPT-4 Vision**: Best for both technical and UI content
   - Consistently high quality
   - Fastest response times
   - Most complete and accurate descriptions

2. **Google Gemini Pro Vision**: Very close second
   - Excellent technical understanding
   - Strong UI analysis
   - Slightly slower than GPT-4

3. **Yi Vision**: Solid performer
   - Good balance of capabilities
   - Consistent performance
   - Competitive speed for UI analysis

4. **DeepInfra BLIP**: Basic but reliable
   - Good for simple descriptions
   - Less technical depth
   - Competitive speed for code analysis

### Cost Considerations
- GPT-4 Vision typically most expensive
- Yi Vision and BLIP offer good value for basic tasks
- Gemini provides excellent value considering performance

### Recommendations
- **Technical Documentation**: GPT-4 or Gemini
- **UI Analysis**: GPT-4 or Yi Vision
- **Cost-Sensitive**: Yi Vision or BLIP
- **Balanced**: Gemini for good performance/cost ratio
