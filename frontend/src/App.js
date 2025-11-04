import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [predictions, setPredictions] = useState([]);
  const [neuralPredictions, setNeuralPredictions] = useState([]);
  const [bestCombo, setBestCombo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('neural');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [predRes, neuralRes, comboRes] = await Promise.all([
        axios.get('/predictions'),
        axios.get('/predictions/neural'),
        axios.get('/best-combo')
      ]);
      
      setPredictions(predRes.data.predictions || []);
      setNeuralPredictions(neuralRes.data.predictions || []);
      setBestCombo(comboRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Erro ao buscar dados:', error);
      setLoading(false);
    }
  };

  const getConfidenceColor = (confidence) => {
    switch(confidence) {
      case 'Muito Alta': return 'text-green-600 bg-green-100';
      case 'Alta': return 'text-green-600 bg-green-100';
      case 'Média': return 'text-yellow-600 bg-yellow-100';
      case 'Baixa': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Carregando previsões...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">
            ⚽ Previsões de Futebol IA
          </h1>
          <p className="text-gray-600 mt-2">
            Análise inteligente com Machine Learning e Redes Neurais
          </p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('neural')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'neural'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                🧠 Previsões IA (Ensemble)
              </button>
              <button
                onClick={() => setActiveTab('stats')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'stats'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                📊 Análise Estatística
              </button>
              <button
                onClick={() => setActiveTab('combo')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'combo'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                🎯 Melhor Combinação
              </button>
            </nav>
          </div>
        </div>

        {/* Neural Predictions */}
        {activeTab === 'neural' && (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">🧠 Ensemble de Modelos IA</h3>
              <p className="text-blue-700 text-sm">
                Combina Análise Estatística + Rede Neural + Random Forest para máxima precisão
              </p>
            </div>
            
            <div className="grid gap-6 md:grid-cols-2">
              {neuralPredictions.map((pred, index) => (
                <div key={index} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">{pred.match}</h3>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(pred.confidence)}`}>
                      {pred.confidence}
                    </span>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="bg-gray-50 rounded p-3">
                      <p className="font-medium text-gray-900 mb-2">🎯 Melhor Aposta:</p>
                      <p className="text-blue-600 font-semibold">{pred.best_bet[0]}</p>
                      <p className="text-sm text-gray-600">Probabilidade: {(pred.best_bet[1] * 100).toFixed(1)}%</p>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Casa: {(pred.prediction.home_win_prob * 100).toFixed(1)}%</p>
                        <p className="text-gray-600">Empate: {(pred.prediction.draw_prob * 100).toFixed(1)}%</p>
                        <p className="text-gray-600">Fora: {(pred.prediction.away_win_prob * 100).toFixed(1)}%</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Over 2.5: {(pred.prediction.over_2_5_prob * 100).toFixed(1)}%</p>
                        <p className="text-gray-600">Modelos: {pred.models_used.length}</p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Statistical Predictions */}
        {activeTab === 'stats' && (
          <div className="grid gap-6 md:grid-cols-2">
            {predictions.map((pred, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">{pred.game}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(pred.confidence)}`}>
                    {pred.confidence}
                  </span>
                </div>
                
                <div className="space-y-3">
                  <div className="bg-gray-50 rounded p-3">
                    <p className="font-medium text-gray-900 mb-1">📈 Previsão:</p>
                    <p className="text-blue-600 font-semibold">{pred.prediction}</p>
                    <p className="text-sm text-gray-600">Probabilidade: {(pred.probability * 100).toFixed(1)}%</p>
                  </div>
                  
                  {pred.expected_goals && (
                    <p className="text-sm text-gray-600">
                      Gols esperados: {pred.expected_goals}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Best Combo */}
        {activeTab === 'combo' && bestCombo && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">🎯 Melhor Combinação do Dia</h3>
            
            {bestCombo.games && bestCombo.games.length > 0 ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-green-50 rounded p-4 text-center">
                    <p className="text-green-600 font-semibold text-lg">{bestCombo.total_odds}</p>
                    <p className="text-green-700 text-sm">Odds Total</p>
                  </div>
                  <div className="bg-blue-50 rounded p-4 text-center">
                    <p className="text-blue-600 font-semibold text-lg">{bestCombo.expected_return}</p>
                    <p className="text-blue-700 text-sm">Retorno Esperado</p>
                  </div>
                  <div className="bg-purple-50 rounded p-4 text-center">
                    <p className="text-purple-600 font-semibold text-lg">{bestCombo.confidence}</p>
                    <p className="text-purple-700 text-sm">Confiança</p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  {bestCombo.games.map((game, index) => (
                    <div key={index} className="border rounded p-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="font-medium">{game.match}</p>
                          <p className="text-blue-600">{game.bet}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold">{game.odds}</p>
                          <p className="text-sm text-gray-600">{(game.probability * 100).toFixed(1)}%</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-gray-600">Nenhuma combinação segura encontrada hoje.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;