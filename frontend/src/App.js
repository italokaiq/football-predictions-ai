import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [predictions, setPredictions] = useState([]);
  const [neuralPredictions, setNeuralPredictions] = useState([]);
  const [bestCombo, setBestCombo] = useState(null);
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('games');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [gamesRes, predRes, neuralRes, comboRes] = await Promise.all([
        axios.get('/games'),
        axios.get('/predictions'),
        axios.get('/predictions/neural'),
        axios.get('/best-combo')
      ]);
      
      setGames(gamesRes.data.games || []);
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
            Premier League • La Liga • Serie A • Brasileirão • Liga Argentina
          </p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('games')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'games'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                🏆 Jogos de Hoje
              </button>
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

        {/* Games Today */}
        {activeTab === 'games' && (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-900 mb-2">🏆 Jogos de Hoje</h3>
              <p className="text-green-700 text-sm">
                Premier League • La Liga • Serie A • Brasileirão • Liga Argentina
              </p>
            </div>
            
            {games.length > 0 ? (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {games.map((game, index) => (
                  <div key={index} className="bg-white rounded-lg shadow-md p-4">
                    <div className="text-center">
                      <div className="text-xs text-gray-500 mb-2">{game.competition}</div>
                      <div className="font-semibold text-gray-900 mb-1">
                        {game.homeTeam}
                      </div>
                      <div className="text-gray-600 text-sm mb-1">vs</div>
                      <div className="font-semibold text-gray-900 mb-2">
                        {game.awayTeam}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(game.date).toLocaleTimeString('pt-BR', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                      <div className={`inline-block px-2 py-1 rounded text-xs mt-2 ${
                        game.status === 'SCHEDULED' ? 'bg-blue-100 text-blue-800' :
                        game.status === 'LIVE' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {game.status === 'SCHEDULED' ? 'Agendado' :
                         game.status === 'LIVE' ? 'Ao Vivo' : game.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600">Nenhum jogo encontrado hoje nas ligas selecionadas</p>
                <p className="text-sm text-gray-500 mt-2">Verifique novamente mais tarde</p>
              </div>
            )}
          </div>
        )}

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
          <div className="space-y-6">
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h3 className="font-semibold text-purple-900 mb-2">📊 Análise das Principais Ligas</h3>
              <p className="text-purple-700 text-sm">
                Previsões baseadas em estatísticas históricas e forma recente dos times
              </p>
            </div>
            
            <div className="grid gap-6 md:grid-cols-2">
              {predictions.map((pred, index) => (
                <div key={index} className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{pred.game}</h3>
                      {pred.league && <p className="text-sm text-gray-500">{pred.league}</p>}
                    </div>
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