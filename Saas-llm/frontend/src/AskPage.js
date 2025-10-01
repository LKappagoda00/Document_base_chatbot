import React, { useState } from "react";
import axios from "axios";

function AskPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [references, setReferences] = useState([]);

  const handleAsk = async () => {
    try {
      const res = await axios.post(
        "/query/ask",
        { question },
        { headers: { Authorization: `Bearer <JWT>` } }
      );
      setAnswer(res.data.answer);
      setReferences(res.data.references || []);
    } catch (err) {
      setAnswer("Error getting answer.");
      setReferences([]);
    }
  };

  return (
    <div className="p-8 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Ask a Question</h1>
      <input
        type="text"
        className="border px-2 py-1 w-full"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Type your question..."
      />
      <button className="bg-green-500 text-white px-4 py-2 mt-2" onClick={handleAsk}>
        Ask
      </button>
      <div className="mt-4">
        <strong>Answer:</strong>
        <div className="bg-gray-100 p-2 mt-2">{answer}</div>
        {references.length > 0 && (
          <div className="mt-4">
            <strong>References:</strong>
            <ul className="list-disc ml-6">
              {references.map((ref, i) => (
                <li key={i}>{ref}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default AskPage;
