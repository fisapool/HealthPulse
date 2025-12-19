
import { GoogleGenAI, Type } from "@google/genai";
import { Facility } from "../types";

// Use Vite's import.meta.env for environment variables
const apiKey = import.meta.env.GEMINI_API_KEY || '';
const ai = apiKey ? new GoogleGenAI({ apiKey }) : null;

export const analyzeSpatialDensity = async (facilities: Facility[]) => {
  if (!ai) {
    console.warn('Gemini API key not configured. Skipping spatial analysis.');
    return "Gemini API key not configured. Please set GEMINI_API_KEY in your environment variables.";
  }

  const prompt = `
    Analyze the following healthcare facilities spatial data:
    ${JSON.stringify(facilities.map(f => ({ name: f.name, type: f.type, loc: f.location })))}

    Provide a concise summary of the healthcare coverage density, identifying any potential "blind spots" or highly clustered areas based on the coordinates provided.
  `;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: prompt,
      config: {
        systemInstruction: "You are a geospatial healthcare analyst specializing in Malaysian and Southeast Asian healthcare infrastructure. Focus on analyzing healthcare facility distribution, coverage density, and identifying service gaps in Malaysia."
      }
    });
    return response.text;
  } catch (error) {
    console.error("Gemini Analysis Error:", error);
    return "Error generating spatial analysis.";
  }
};

export const suggestDeduplication = async (facilities: Facility[]) => {
  if (!ai) {
    console.warn('Gemini API key not configured. Skipping deduplication suggestions.');
    return [];
  }

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-pro-preview",
      contents: `Look at these facilities and suggest which ones might be duplicates based on name and proximity. Data: ${JSON.stringify(facilities)}`,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.ARRAY,
          items: {
            type: Type.OBJECT,
            properties: {
              pair: { type: Type.ARRAY, items: { type: Type.STRING } },
              confidence: { type: Type.NUMBER },
              reason: { type: Type.STRING }
            },
            required: ["pair", "confidence", "reason"]
          }
        }
      }
    });

    return JSON.parse(response.text || '[]');
  } catch (error) {
    console.error("Gemini Deduplication Error:", error);
    return [];
  }
};
