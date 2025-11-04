import numpy as np
from stats_analyzer import StatsAnalyzer
from neural_predictor import NeuralPredictor
from ml_predictor import FootballPredictor

class EnsemblePredictor:
    def __init__(self):
        self.stats_analyzer = StatsAnalyzer()
        self.neural_predictor = NeuralPredictor()
        self.ml_predictor = FootballPredictor()
        
    def predict_match_ensemble(self, home_team, away_team):
        """Combina previsões de múltiplos modelos"""
        predictions = {}
        weights = {}
        
        # Análise estatística (peso: 0.3)
        try:
            stats_pred = self.stats_analyzer.calculate_match_probabilities(home_team, away_team)
            predictions['stats'] = stats_pred
            weights['stats'] = 0.3
        except:
            pass
        
        # Rede Neural (peso: 0.4)
        try:
            neural_pred = self.neural_predictor.predict_match(home_team, away_team)
            if neural_pred:
                predictions['neural'] = neural_pred
                weights['neural'] = 0.4
        except:
            pass
        
        # Random Forest (peso: 0.3)
        try:
            ml_pred = self.ml_predictor.predict_match(home_team, away_team)
            if ml_pred:
                predictions['ml'] = ml_pred
                weights['ml'] = 0.3
        except:
            pass
        
        if not predictions:
            return self._default_prediction()
        
        # Combina previsões
        ensemble_result = self._combine_predictions(predictions, weights)
        ensemble_result['models_used'] = list(predictions.keys())
        ensemble_result['ensemble_confidence'] = self._calculate_ensemble_confidence(predictions)
        
        return ensemble_result
    
    def _combine_predictions(self, predictions, weights):
        """Combina previsões usando média ponderada"""
        combined = {
            'home_win_prob': 0,
            'draw_prob': 0,
            'away_win_prob': 0,
            'over_2_5_prob': 0
        }
        
        total_weight = sum(weights.values())
        
        for model, pred in predictions.items():
            weight = weights.get(model, 0) / total_weight
            
            combined['home_win_prob'] += pred.get('home_win_prob', 0) * weight
            combined['draw_prob'] += pred.get('draw_prob', 0) * weight
            combined['away_win_prob'] += pred.get('away_win_prob', 0) * weight
            combined['over_2_5_prob'] += pred.get('over_2_5_prob', 0) * weight
        
        # Normaliza probabilidades de resultado
        result_sum = combined['home_win_prob'] + combined['draw_prob'] + combined['away_win_prob']
        if result_sum > 0:
            combined['home_win_prob'] /= result_sum
            combined['draw_prob'] /= result_sum
            combined['away_win_prob'] /= result_sum
        
        # Arredonda valores
        for key in combined:
            combined[key] = round(combined[key], 3)
        
        return combined
    
    def _calculate_ensemble_confidence(self, predictions):
        """Calcula confiança do ensemble baseada na concordância dos modelos"""
        if len(predictions) < 2:
            return 'Baixa'
        
        # Verifica concordância nas previsões principais
        home_wins = []
        over_2_5s = []
        
        for pred in predictions.values():
            home_wins.append(pred.get('home_win_prob', 0))
            over_2_5s.append(pred.get('over_2_5_prob', 0))
        
        # Calcula desvio padrão (menor = maior concordância)
        home_std = np.std(home_wins)
        over_std = np.std(over_2_5s)
        
        avg_std = (home_std + over_std) / 2
        
        if avg_std < 0.1:
            return 'Muito Alta'
        elif avg_std < 0.15:
            return 'Alta'
        elif avg_std < 0.25:
            return 'Média'
        else:
            return 'Baixa'
    
    def get_best_predictions(self):
        """Retorna as melhores previsões do ensemble para times disponíveis"""
        matches = [
            ('Real Madrid', 'Barcelona'),
            ('Manchester City', 'Liverpool'),
            ('Bayern Munich', 'PSG'),
            ('Chelsea', 'Arsenal')
        ]
        
        best_predictions = []
        
        for home_team, away_team in matches:
            pred = self.predict_match_ensemble(home_team, away_team)
            
            if pred:
                # Determina melhor aposta
                best_bet = self._determine_best_bet(pred)
                
                best_predictions.append({
                    'match': f'{home_team} vs {away_team}',
                    'prediction': pred,
                    'best_bet': best_bet,
                    'models_used': pred.get('models_used', []),
                    'confidence': pred.get('ensemble_confidence', 'Baixa')
                })
        
        return best_predictions
    
    def _determine_best_bet(self, prediction):
        """Determina a melhor aposta baseada nas probabilidades"""
        bets = [
            ('Over 2.5 gols', prediction['over_2_5_prob']),
            ('Under 2.5 gols', 1 - prediction['over_2_5_prob']),
            ('Vitória Casa', prediction['home_win_prob']),
            ('Empate', prediction['draw_prob']),
            ('Vitória Fora', prediction['away_win_prob'])
        ]
        
        # Filtra apostas com probabilidade > 50%
        good_bets = [(bet, prob) for bet, prob in bets if prob > 0.5]
        
        if good_bets:
            return max(good_bets, key=lambda x: x[1])
        else:
            return max(bets, key=lambda x: x[1])
    
    def _default_prediction(self):
        """Previsão padrão quando nenhum modelo funciona"""
        return {
            'home_win_prob': 0.40,
            'draw_prob': 0.30,
            'away_win_prob': 0.30,
            'over_2_5_prob': 0.50,
            'models_used': [],
            'ensemble_confidence': 'Baixa'
        }

if __name__ == "__main__":
    ensemble = EnsemblePredictor()
    
    # Teste
    result = ensemble.predict_match_ensemble('Real Madrid', 'Barcelona')
    print("Previsão Ensemble:")
    for key, value in result.items():
        print(f"  {key}: {value}")